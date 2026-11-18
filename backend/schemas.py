from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Numero = Annotated[float, Field(allow_inf_nan=False)]

class LeituraEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estacao_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    luz: Literal[0, 1]
    estado: Literal["Claro", "Escuro"]
    temperatura: Numero | None = Field(default=None, ge=-40, le=80)
    umidade: Numero | None = Field(default=None, ge=0, le=100)
    gas: int | None = Field(default=None, ge=0, le=4095)
    pressao: Numero | None = Field(default=None, ge=300, le=1100)
    temperatura_bmp: Numero | None = Field(default=None, ge=-40, le=85)
    bmp_conectado: bool

    @model_validator(mode="after")
    def validar_estados(self):
        if self.estado != ("Claro" if self.luz == 0 else "Escuro"):
            raise ValueError("Estado da luz inconsistente")
        if self.bmp_conectado != (self.pressao is not None and self.temperatura_bmp is not None):
            raise ValueError("Estado do BMP280 inconsistente")
        if not self.bmp_conectado and (self.pressao is not None or self.temperatura_bmp is not None):
            raise ValueError("BMP280 desconectado deve informar valores nulos")
        return self

class LeituraSaida(LeituraEntrada):
    id: int
    recebido_em: str
