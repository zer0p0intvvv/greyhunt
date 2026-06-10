import os

_client = None
_resolved_model = None


def _resolve():
    api_key = (
        os.environ.get("GMH_LLM_API_KEY")
        or os.environ.get("VOLCENGINE_API_KEY")
        or os.environ.get("ARK_API_KEY")
        or os.environ.get("MAAS_API_KEY")
        or ""
    )
    base_url = (
        os.environ.get("GMH_LLM_BASE_URL")
        or os.environ.get("ARK_BASE_URL")
        or os.environ.get("MAAS_BASE_URL")
        or "https://ark.cn-beijing.volces.com/api/v3"
    )
    model = (
        os.environ.get("GMH_LLM_MODEL")
        or os.environ.get("ARK_MODEL")
        or os.environ.get("MAAS_MODEL")
        or ""
    )
    headers = {}
    if os.environ.get("MAAS_USER_EMAIL"):
        headers["x-maas-user-email"] = os.environ["MAAS_USER_EMAIL"]
    if os.environ.get("MAAS_APP_ID"):
        headers["x-maas-app-id"] = os.environ["MAAS_APP_ID"]
    return api_key, base_url, model, headers


def _get_client():
    global _client, _resolved_model
    if _client is not None:
        return _client
    try:
        from openai import OpenAI
    except ImportError:
        print("[LLM] 需要安装 openai: pip3 install openai")
        return None
    api_key, base_url, model, headers = _resolve()
    _resolved_model = model
    if not api_key:
        print(
            "[LLM] 未配置 API key (设置 VOLCENGINE_API_KEY / ARK_API_KEY / MAAS_API_KEY)"
        )
        return None
    _client = OpenAI(
        api_key=api_key, base_url=base_url, default_headers=headers or None
    )
    return _client


def llm(prompt, model=None, temperature=0.2, max_tokens=800):
    client = _get_client()
    if client is None:
        return None
    model = model or _resolved_model or os.environ.get("GMH_LLM_MODEL", "")
    if not model:
        print("[LLM] 未配置模型 (设置 GMH_LLM_MODEL 或 ARK 推理接入点 ep-...)")
        return None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[LLM] 调用失败: {e}")
        return None


if __name__ == "__main__":
    print("测试 LLM 连接...")
    print("返回:", llm("用一句话介绍你自己"))
