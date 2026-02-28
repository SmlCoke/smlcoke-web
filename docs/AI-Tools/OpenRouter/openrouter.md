# OpenRouter



## I OpenRouter
由 OpenRouter 提供 API Key.

### II Deno Deploy
在 Deno Deploy部署了一个二次转发节点（https://important-camel-97.smlcoke.deno.net）：
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
Free Plan, 每月 10, 000k 次请求

!!! note "Important"
    此时已经可以通过 `https://important-camel-97.smlcoke.deno.net` 这个地址访问 OpenRouter 的 API 了，但由于 Deno Deploy 的服务器在国外，访问速度可能不太稳定，所以我们还需要一个国内的中转结点。
    如果想要直接通过这个域名调用大模型，这里以`Claude Code`为例（已经测试通过`Claude Opus 4.6`）：
    设置**临时**环境变量（**powershell语法**）
    ```ps
    $env:ANTHROPIC_AUTH_TOKEN=""
    $env:ANTHROPIC_BASE_URL="https://important-camel-97.smlcoke.deno.net"
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

**创建Cloudflare Worker**：编写并部署 `smlcoke-ai-worker`(worker的名字) 代码，通过绑定子域名 `api.smlcoke.com`，搭建一个属于自己的、国内可直接访问的代理服务器：
```js
export default {
  async fetch(request) {
    const url = new URL(request.url);
    
    // 🔥 将这里的网址替换成你刚才在 Deno 生成的真实域名 🔥
    // 注意：保留 https://，且结尾不要带斜杠
    const denoUrl = "https://important-camel-97.smlcoke.deno.net"; 
    
    // 拼装最终发送给 Deno 的地址
    const targetUrl = `${denoUrl}${url.pathname}${url.search}`;

    // Cloudflare 只做国内加速的搬运工，什么头都不改，原封不动发给 Deno
    return fetch(new Request(targetUrl, request));
  }
};
```


!!! warning "Bug"
    依旧无法在 `Claude Code` 中使用 `Gemini` 和 `GPT` 模型，怀疑是 `Claude Code` 这边对返回的响应做了某些处理，导致无法正确解析响应中的模型列表。
    通过`curl.exe https://api.smlcoke.com/api/v1/models -H "Authorization: Bearer sk-or-v1-..."`，可以清楚`OpenRouter`的 API ==确实返回了完整的模型列表==。 