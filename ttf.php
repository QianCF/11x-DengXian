<?php
// 1. 设置跨域头（CORS）
header('Access-Control-Allow-Origin: *');  // 允许所有域名访问，生产环境可改为特定域名
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Origin, Content-Type, Accept');

// 2. 处理预检请求（OPTIONS）
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// 3. 设置字体文件的正确 MIME 类型
header('Content-Type: application/x-font-ttf');
// 或使用更通用的: header('Content-Type: application/octet-stream');

// 4. 设置缓存策略（可选，提高性能）
header('Cache-Control: public, max-age=86400'); // 缓存1天

// 5. 字体文件路径（与 ttf.php 在同一目录）
$fontFile = __DIR__ . '/Deng_11x.ttf';

// 6. 检查文件是否存在
if (!file_exists($fontFile)) {
    http_response_code(404);
    echo 'Font file not found. Make sure Deng_11x.ttf is in the same directory as ttf.php';
    exit();
}

// 7. 输出文件内容
readfile($fontFile);