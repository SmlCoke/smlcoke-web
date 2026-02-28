# 🔐 Rust 交互式加密工具

这是 SmlCoke 的第一个 Rust 项目。通过 WebAssembly 技术，这段加解密逻辑直接运行在你的浏览器中，**不经过服务器**，极速且隐私。

<div id="crypto-app" style="background: #fdfdfd; padding: 25px; border: 1px solid #ddd; border-radius: 15px; margin-top: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); color: #333;">
    <h3 style="margin-top: 0; color: #1980a8;">CipherY</h3>
    
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px;">算法：</label>
        <select id="algo" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc;">
            <option value="caesar">Caesar</option>
            <option value="rot13">ROT13</option>
            <option value="vigenere">Vigenere</option>
            <option value="xor">Xor</option>
            <option value="rail_fence">RailFence</option>
        </select>
    </div>

    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px;">密钥：</label>
        <input type="text" id="key" value="3" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc;" placeholder="Caesar/ROT13 填数字，Vigenere 填字母如 LEMON">
    </div>

    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px;">输入文本：</label>
        <textarea id="inputText" rows="4" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc; font-family: monospace;" placeholder="Hello, Rust!"></textarea>
    </div>

    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <button id="encryptBtn" style="flex: 1; padding: 12px; background: #23a6d5; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">加密 (Encrypt)</button>
        <button id="decryptBtn" style="flex: 1; padding: 12px; background: #e73c7e; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">解密 (Decrypt)</button>
    </div>

    <hr style="border: 0.5px solid #eee; margin-bottom: 20px;">

    <div>
        <label style="font-weight: bold; display: block; margin-bottom: 5px;">输出结果：</label>
        <textarea id="outputText" rows="4" readonly style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #eee; background: #f9f9f9; color: #1980a8; font-family: monospace;"></textarea>
    </div>
</div>

<script type="module">
    // 注意路径：这里引用的是当前目录 pkg 文件夹下的 js 文件
    import init, { wasm_encrypt, wasm_decrypt } from '../pkg/ciphery.js';

    async function start() {
        try {
            // 初始化 WASM
            await init();
            console.log("Ciphery WASM initialized!");

            const encryptBtn = document.getElementById('encryptBtn');
            const decryptBtn = document.getElementById('decryptBtn');
            const inputText = document.getElementById('inputText');
            const outputText = document.getElementById('outputText');
            const algo = document.getElementById('algo');
            const key = document.getElementById('key');

            // 绑定加密逻辑
            encryptBtn.onclick = () => {
                const res = wasm_encrypt(algo.value, inputText.value, key.value);
                outputText.value = res;
            };

            // 绑定解密逻辑
            decryptBtn.onclick = () => {
                const res = wasm_decrypt(algo.value, inputText.value, key.value);
                outputText.value = res;
            };

        } catch (err) {
            console.error("WASM Load Error: ", err);
        }
    }

    start();
</script>