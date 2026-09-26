# OpenRouter



## I OpenRouter
由 OpenRouter 提供 API Key.

### II Deno Deploy
在 Deno Deploy部署了一个二次转发节点：
点击`New Playground`，在出现的代码框中写入：
```ts
Deno.serve(async (request) => {
  const url = new URL(request.url);
  let path = url.pathname;
  
  // 智能补全 Claude Code 需要的路径
  if (path.endsWith("/messages")) path = "/api/v1/messages";
  else if (!path.startsWith("/api/v1")) path = "/api/v1" + path;

  // 目标直接锁定 OpenRouter
  const targetUrl = `https://openrouter.ai${path}`;
  const headers = new Headers(request.headers);
  
  // 致命杀招：彻底抹除一切可能暴露真实地理位置的 Header
  headers.delete("x-forwarded-for");
  headers.delete("x-real-ip");
  headers.delete("cf-connecting-ip");
  
  // 兼容 Claude Code 发送的 API Key
  const auth = headers.get("x-api-key");
  if (auth) headers.set("authorization", `Bearer ${auth}`);

  return fetch(targetUrl, {
    method: request.method,
    headers,
    body: request.body
  });
});
```
写入之后，点击`Deploy`，就会得到一个二级域名（以下记作`xxx.deno.net`），这个域名就是我们**访问 OpenRouter API 的入口**了。

Free Plan, 每月 10, 000k 次请求

!!! note "Important"
    此时已经可以通过 `xxx.deno.net` 这个地址访问 OpenRouter 的 API 了，但由于 Deno Deploy 的服务器在国外，访问速度可能不太稳定，所以我们还需要一个国内的中转结点。
    如果想要直接通过这个域名调用大模型，这里以`Claude Code`为例（已经测试通过`Claude Opus 4.6`）：
    设置**临时**环境变量（**powershell语法**）
    ```ps
    $env:ANTHROPIC_AUTH_TOKEN=""
    $env:ANTHROPIC_BASE_URL="xxx.deno.net"
    $env:ANTHROPIC_API_KEY="sk-or-v1..."
    $env:ANTHROPIC_MODEL="anthropic/claude-opus-4.6"
    $env:ANTHROPIC_DEFAULT_OPUS_MODEL="anthropic/claude-opus-4.6"
    $env:ANTHROPIC_DEFAULT_SONNET_MODEL="anthropic/claude-sonnet-4.6"
    $env:ANTHROPIC_DEFAULT_HAIKU_MODEL="anthropic/claude-haiku-4.5"
    $env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"
    ```
    然后启动 `Claude Code` 即可正常使用。
    ==但是这里有一个问题：`Gemini`, `GPT`无法使用，暂时不清楚原因。==

### III Cloudflare Worker
在`Build/Compute/Worker&Pages`界面，点击`Create application`，选择`Start with hello world`，进入编辑界面，为你的 worker 起一个名字，然后**替换默认代码为以下代码**，点击`Deploy`**部署**：

```js
export default {
  async fetch(request) {
    const url = new URL(request.url);
    
    // 🔥 将这里的网址替换成你刚才在 Deno 生成的真实域名 🔥
    // 注意：保留 https://，且结尾不要带斜杠
    const denoUrl = "xxx.deno.net"; 
    
    // 拼装最终发送给 Deno 的地址
    const targetUrl = `${denoUrl}${url.pathname}${url.search}`;

    // Cloudflare 只做国内加速的搬运工，什么头都不改，原封不动发给 Deno
    return fetch(new Request(targetUrl, request));
  }
};
```

接下来需要**绑定域名**，在 `Settings` 界面，`Domains & Routes` 这一栏，留意它的右侧或下方，会有一个 "+ Add" 或者 "`Add Custom Domain`" (添加自定义域) 的按钮。
点击它，在弹出的输入框中填入你想要的子域名，比如：`api.smlcoke.com`
点击 "`Add domain`" (添加域) 进行确认。

!!! note '提示'
    `smlcoke.com` 域名原本就托管在 Cloudflare，系统会自动帮你添加 DNS 解析记录并配置好 SSL 证书。
    如果此前没有域名，Cloudflare 也提供免费的二级域名，直接使用 `xxx.workers.dev` 这样的地址也是完全没问题的。
  

!!! warning "Bug"
    依旧无法在 `Claude Code` 中使用 `Gemini` 和 `GPT` 模型，怀疑是 `Claude Code` 这边对返回的响应做了某些处理，导致无法正确解析响应中的模型列表。
    通过`curl.exe https://api.smlcoke.com/api/v1/models -H "Authorization: Bearer sk-or-v1-..."`，可以清楚`OpenRouter`的 API ==确实返回了完整的模型列表==。 


