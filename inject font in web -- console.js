(function() {
    const fontUrl = 'http://127.0.0.1:8081/ttf.php';
    const fontFamilyName = '等线11x'; 
    const style = document.createElement('style');
    style.textContent = `
        @font-face {
            font-family: '${fontFamilyName}';
            src: url('${fontUrl}') format('truetype');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }
        * {
            font-family: '${fontFamilyName}', 'sans-serif' !important;
        }
    `;
    document.head.appendChild(style);
})();