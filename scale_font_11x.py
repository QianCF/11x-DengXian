#!/usr/bin/env python3
"""
将 TTF/OTF 字体中所有字形轮廓与度量放大指定倍数，生成新字体文件。

依赖: pip install fonttools

用法:
    python scale_font_8x.py Deng.ttf
    python scale_font_8x.py Deng.ttf -o Deng_8x.ttf -s 8 --rename-suffix 8x
    python scale_font_8x.py Deng.ttf --family-en MyFont --family-zh 我的字体
    python scale_font_8x.py Deng_8x.ttf --rename-only --family-en DengXian8x --family-zh 等线8x
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

# Windows 平台常用语言 ID
_LANG_EN = 0x409
_LANG_ZH = 0x804
_PLATFORM_WINDOWS = 3
_ENCODING_UNICODE = 1


def _make_ps_name(family: str, subfamily: str) -> str:
    """生成 PostScript 名称（仅字母数字与连字符）。"""
    base = "".join(c for c in family if c.isalnum())
    if not base:
        raise ValueError(f"无法从族名生成 PostScript 名称: {family!r}")
    if subfamily and subfamily.lower() != "regular":
        suffix = "".join(c for c in subfamily if c.isalnum())
        return f"{base}-{suffix}"
    return base


def rename_font(
    font: TTFont,
    *,
    family_en: str | None = None,
    family_zh: str | None = None,
    subfamily: str | None = None,
    suffix: str | None = None,
) -> None:
    """
    更新 name 表中的族名、全名、PostScript 名等，使系统字体列表显示新名称。

    family_en / family_zh 未指定时，可在原族名后追加 suffix（如 \"8x\"）。
    """
    name_table = font["name"]
    old_en = name_table.getBestFamilyName()
    old_zh = _get_name(name_table, 1, _LANG_ZH)
    old_sub = name_table.getBestSubFamilyName() or "Regular"
    sub = subfamily or old_sub

    if family_en is None:
        if not old_en:
            raise ValueError("字体缺少英文族名，请用 --family-en 指定新名称")
        family_en = f"{old_en}{suffix}" if suffix else old_en

    if family_zh is None:
        if old_zh:
            family_zh = f"{old_zh}{suffix}" if suffix else old_zh
        else:
            family_zh = family_en

    full_en = f"{family_en} {sub}"
    full_zh = f"{family_zh} {sub}"
    ps_name = _make_ps_name(family_en, sub)

    for lang, family, full in (
        (_LANG_EN, family_en, full_en),
        (_LANG_ZH, family_zh, full_zh),
    ):
        name_table.setName(
            family, 1, _PLATFORM_WINDOWS, _ENCODING_UNICODE, lang
        )
        name_table.setName(
            sub, 2, _PLATFORM_WINDOWS, _ENCODING_UNICODE, lang
        )
        name_table.setName(
            full, 3, _PLATFORM_WINDOWS, _ENCODING_UNICODE, lang
        )
        name_table.setName(
            full, 4, _PLATFORM_WINDOWS, _ENCODING_UNICODE, lang
        )

    name_table.setName(
        ps_name, 6, _PLATFORM_WINDOWS, _ENCODING_UNICODE, _LANG_EN
    )
    print(f"  字体名称: {family_en} / {family_zh} (PostScript: {ps_name})")


def _get_name(name_table, name_id: int, lang_id: int) -> str | None:
    rec = name_table.getName(nameID=name_id, platformID=_PLATFORM_WINDOWS,
                             platEncID=_ENCODING_UNICODE, langID=lang_id)
    return rec.toUnicode() if rec else None


def _scale_int(value: int, factor: float) -> int:
    return int(round(value * factor))


def _scale_glyph(glyph, factor: float) -> None:
    if glyph.numberOfContours == 0:
        return

    if glyph.isComposite():
        for comp in glyph.components:
            comp.x = _scale_int(comp.x, factor)
            comp.y = _scale_int(comp.y, factor)
            # transform 为 F2.14 比例/旋转，不随字形坐标系等比放大
    else:
        glyph.coordinates.transform(((factor, 0, 0), (0, factor, 0)))


def _scale_hmtx(font: TTFont, factor: float) -> None:
    hmtx = font["hmtx"]
    for name in font.getGlyphOrder():
        aw, lsb = hmtx[name]
        hmtx[name] = (_scale_int(aw, factor), _scale_int(lsb, factor))


def _scale_vmtx(font: TTFont, factor: float) -> None:
    if "vmtx" not in font:
        return
    vmtx = font["vmtx"]
    for name in font.getGlyphOrder():
        aw, tsb = vmtx[name]
        vmtx[name] = (_scale_int(aw, factor), _scale_int(tsb, factor))


def _scale_hhea(font: TTFont, factor: float) -> None:
    hhea = font["hhea"]
    hhea.ascent = _scale_int(hhea.ascent, factor)
    hhea.descent = _scale_int(hhea.descent, factor)
    hhea.lineGap = _scale_int(hhea.lineGap, factor)
    hhea.advanceWidthMax = _scale_int(hhea.advanceWidthMax, factor)
    hhea.minLeftSideBearing = _scale_int(hhea.minLeftSideBearing, factor)
    hhea.minRightSideBearing = _scale_int(hhea.minRightSideBearing, factor)
    hhea.xMaxExtent = _scale_int(hhea.xMaxExtent, factor)
    hhea.caretOffset = _scale_int(hhea.caretOffset, factor)


def _scale_vhea(font: TTFont, factor: float) -> None:
    if "vhea" not in font:
        return
    vhea = font["vhea"]
    vhea.ascent = _scale_int(vhea.ascent, factor)
    vhea.descent = _scale_int(vhea.descent, factor)
    vhea.lineGap = _scale_int(vhea.lineGap, factor)
    vhea.advanceHeightMax = _scale_int(vhea.advanceHeightMax, factor)
    vhea.minTopSideBearing = _scale_int(vhea.minTopSideBearing, factor)
    vhea.minBottomSideBearing = _scale_int(vhea.minBottomSideBearing, factor)
    vhea.yMaxExtent = _scale_int(vhea.yMaxExtent, factor)
    vhea.caretOffset = _scale_int(vhea.caretOffset, factor)


def _scale_os2(font: TTFont, factor: float) -> None:
    os2 = font["OS/2"]
    os2.sTypoAscender = _scale_int(os2.sTypoAscender, factor)
    os2.sTypoDescender = _scale_int(os2.sTypoDescender, factor)
    os2.sTypoLineGap = _scale_int(os2.sTypoLineGap, factor)
    os2.usWinAscent = _scale_int(os2.usWinAscent, factor)
    os2.usWinDescent = _scale_int(os2.usWinDescent, factor)
    if os2.sxHeight:
        os2.sxHeight = _scale_int(os2.sxHeight, factor)
    if os2.sCapHeight:
        os2.sCapHeight = _scale_int(os2.sCapHeight, factor)
    if os2.ySubscriptXSize:
        os2.ySubscriptXSize = _scale_int(os2.ySubscriptXSize, factor)
        os2.ySubscriptYSize = _scale_int(os2.ySubscriptYSize, factor)
        os2.ySubscriptXOffset = _scale_int(os2.ySubscriptXOffset, factor)
        os2.ySubscriptYOffset = _scale_int(os2.ySubscriptYOffset, factor)
        os2.ySuperscriptXSize = _scale_int(os2.ySuperscriptXSize, factor)
        os2.ySuperscriptYSize = _scale_int(os2.ySuperscriptYSize, factor)
        os2.ySuperscriptXOffset = _scale_int(os2.ySuperscriptXOffset, factor)
        os2.ySuperscriptYOffset = _scale_int(os2.ySuperscriptYOffset, factor)
        os2.yStrikeoutSize = _scale_int(os2.yStrikeoutSize, factor)
        os2.yStrikeoutPosition = _scale_int(os2.yStrikeoutPosition, factor)


def _strip_hinting(font: TTFont) -> None:
    """放大后原 TrueType 提示指令不再适用，清除以免渲染异常。"""
    glyf = font["glyf"]
    for glyph in glyf.glyphs.values():
        if getattr(glyph, "program", None) is not None:
            glyph.program.fromBytecode(b"")

    for tag in ("fpgm", "prep", "cvt ", "hdmx", "LTSH"):
        if tag in font:
            del font[tag]


def scale_font(
    input_path: Path,
    output_path: Path,
    factor: float,
    *,
    family_en: str | None = None,
    family_zh: str | None = None,
    subfamily: str | None = None,
    rename_suffix: str | None = None,
) -> None:
    if factor <= 0:
        raise ValueError(f"放大倍数必须为正数，当前为: {factor}")

    font = TTFont(input_path)

    if "glyf" not in font:
        raise ValueError("仅支持 TrueType 轮廓字体（含 glyf 表），本字体不含 glyf 表")

    glyf = font["glyf"]
    glyph_order = font.getGlyphOrder()
    total = len(glyph_order)

    for i, name in enumerate(glyph_order):
        _scale_glyph(glyf[name], factor)
        if (i + 1) % 5000 == 0 or i + 1 == total:
            print(f"  字形轮廓: {i + 1}/{total}", flush=True)

    _scale_hmtx(font, factor)
    _scale_vmtx(font, factor)
    _scale_hhea(font, factor)
    _scale_vhea(font, factor)
    _scale_os2(font, factor)
    _strip_hinting(font)

    if family_en or family_zh or rename_suffix or subfamily:
        rename_font(
            font,
            family_en=family_en,
            family_zh=family_zh,
            subfamily=subfamily,
            suffix=rename_suffix,
        )

    # 保存时由 fontTools 根据放大后的轮廓重算 head/hhea 等边界
    font.recalcBBoxes = True
    print(f"  保存到: {output_path}", flush=True)
    font.save(output_path)
    font.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将字体中所有字形放大指定倍数并输出新字体文件"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="输入字体路径（如 Deng.ttf）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出字体路径（默认: 原文件名_8x.ttf）",
    )
    parser.add_argument(
        "-s",
        "--scale",
        type=float,
        default=11.0,
        help="放大倍数（默认: 11）",
    )
    parser.add_argument(
        "--family-en",
        help="新字体英文族名（如 DengXian8x）",
    )
    parser.add_argument(
        "--family-zh",
        help="新字体中文族名（如 等线8x）",
    )
    parser.add_argument(
        "--subfamily",
        help="字体子族名（默认保持原值，一般为 Regular）",
    )
    parser.add_argument(
        "--rename-suffix",
        help="在原族名后追加后缀（如 8x）；未指定 --family-en/zh 时生效",
    )
    parser.add_argument(
        "--rename-only",
        action="store_true",
        help="仅改名不缩放（需配合 --family-en/zh 或 --rename-suffix）",
    )
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.is_file():
        print(f"错误: 找不到输入文件 {input_path}", file=sys.stderr)
        return 1

    output_path = args.output
    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_{int(args.scale)}x")
    output_path = output_path.resolve()

    rename_suffix = args.rename_suffix
    if (
        rename_suffix is None
        and not args.rename_only
        and not args.family_en
        and not args.family_zh
    ):
        rename_suffix = f"{int(args.scale)}x"

    do_rename = bool(
        args.family_en or args.family_zh or rename_suffix or args.subfamily
    )
    if args.rename_only and not do_rename:
        print("错误: --rename-only 需配合 --family-en/zh 或 --rename-suffix", file=sys.stderr)
        return 1

    print(f"输入: {input_path}")
    print(f"倍数: {args.scale}" + ("（仅改名）" if args.rename_only else ""))
    print(f"输出: {output_path}")

    try:
        if args.rename_only:
            font = TTFont(input_path)
            rename_font(
                font,
                family_en=args.family_en,
                family_zh=args.family_zh,
                subfamily=args.subfamily,
                suffix=rename_suffix,
            )
            font.save(output_path)
            font.close()
        else:
            scale_font(
                input_path,
                output_path,
                args.scale,
                family_en=args.family_en,
                family_zh=args.family_zh,
                subfamily=args.subfamily,
                rename_suffix=rename_suffix if do_rename else None,
            )
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
