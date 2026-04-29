"""FastAPI endpoint that replaces one-provider gpt-pro-mode with ModelPreflight routing."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from model_preflight import ModelGateway, load_config, pro_mode

app = FastAPI(title="ModelPreflight Pro Mode")
config = load_config()
gateway = ModelGateway(config)


class ProModeRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    num_gens: int = Field(8, ge=1, le=100)
    sample_group: str | None = None
    judge_group: str | None = None


@app.post("/pro-mode")
def endpoint(body: ProModeRequest):
    return pro_mode(
        gateway,
        body.prompt,
        n=body.num_gens,
        sample_group=body.sample_group or config.router.default_group,
        judge_group=body.judge_group or config.router.default_group,
    )
