# nexoraAI

## Environment variables

Do not hardcode secrets in source code. Configure them through environment variables.

Required:

- `OPENAI_API_KEY`
- `TELEGRAM_TOKEN`
- `REDIS_URL`
- `BASE_URL`

Optional:

- `TAVILY_API_KEY`
- `ACTION_WEBHOOK_URL`
- `OWNER_ID`
- `MODEL_NAME`
- `APP_NAME`

Example:

```env
TELEGRAM_TOKEN=your_new_bot_token_here
```

For Railway, Docker, and similar platforms, set secrets in the platform environment/variables settings instead of committing them to the repository.
