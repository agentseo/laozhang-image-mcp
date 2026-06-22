# laozhang-image MCP

An [MCP](https://modelcontextprotocol.io) server that exposes **image generation
and editing** through [laozhang.ai](https://api.laozhang.ai/register/?aff_code=ZkDN) — an
OpenAI-compatible API proxy/aggregator. Default model: **`gpt-image-2-vip`**
(flat ~$0.03 per image).

Works with any MCP client (Claude Code, Claude Desktop, etc.). The API key is
read from the environment and never stored in code.

---

## What it does

laozhang.ai mirrors the OpenAI Image API (`/v1/images/generations`,
`/v1/images/edits`) but with its own models and pricing. This server wraps those
endpoints as two MCP tools:

| Tool                                              | Description                                                             |
| ------------------------------------------------- | ----------------------------------------------------------------------- |
| `generate_image(prompt, size, quality, n)`        | Text → image. Saves PNG(s), returns file path **and** source URL.       |
| `edit_image(image_path, prompt, size, mask_path)` | Image → image. Edits an existing picture from a prompt (optional mask). |

`size` accepts presets `1k` / `2k` / `4k`, `square` / `landscape` / `portrait`,
`auto`, or an explicit `WxH` like `1024x1536`.

---

## Install

```bash
git clone https://github.com/agentseo/laozhang-image-mcp.git
cd laozhang-image-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Configure

| Env var             | Default                      | Purpose              |
| ------------------- | ---------------------------- | -------------------- |
| `LAOZHANG_API_KEY`  | — (**required**)             | your laozhang.ai key |
| `LAOZHANG_BASE_URL` | `https://api.laozhang.ai/v1` | API base URL         |
| `LAOZHANG_MODEL`    | `gpt-image-2-vip`            | model id             |
| `LAOZHANG_OUT_DIR`  | `laozhang-images`            | where PNGs are saved |

## Connect to Claude Code

```bash
claude mcp add laozhang-image -s user \
  -e LAOZHANG_API_KEY=sk-your-key \
  -e LAOZHANG_MODEL=gpt-image-2-vip \
  -- /path/to/laozhang-image-mcp/.venv/bin/python \
     /path/to/laozhang-image-mcp/server.py
```

Or edit your config manually — see [`mcp.example.json`](./mcp.example.json).
Verify with `claude mcp list` (expect `✓ connected`).

## Sanity check (plain curl)

```bash
curl https://api.laozhang.ai/v1/images/generations \
  -H "Authorization: Bearer $LAOZHANG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2-vip","prompt":"a red fox","n":1,"size":"1024x1024"}'
```

---

## Русский

MCP-сервер для генерации и редактирования картинок через
[laozhang.ai](https://api.laozhang.ai/register/?aff_code=ZkDN) — OpenAI-совместимый прокси-агрегатор.
Модель по умолчанию **`gpt-image-2-vip`** (~$0.03 за картинку). Подходит для
любого MCP-клиента (Claude Code, Claude Desktop).

**Что делает.** laozhang.ai повторяет формат OpenAI Image API, но со своими
моделями и ценами. Сервер оборачивает это в два инструмента:

- `generate_image(prompt, size, quality, n)` — текст → картинка. Сохраняет PNG,
  возвращает путь к файлу **и** URL.
- `edit_image(image_path, prompt, size, mask_path)` — картинка → картинка.
  Редактирует существующее изображение по описанию (можно с маской).

`size`: пресеты `1k` / `2k` / `4k`, `square` / `landscape` / `portrait`, `auto`,
либо явно `1024x1536`.

**Ключ** не хранится в коде — берётся из переменной окружения `LAOZHANG_API_KEY`
(см. таблицу выше). Установка и подключение — в английской секции.

---

## License

MIT — see [LICENSE](./LICENSE).
