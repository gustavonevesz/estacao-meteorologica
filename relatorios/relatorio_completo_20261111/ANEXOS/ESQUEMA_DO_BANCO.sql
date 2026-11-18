CREATE INDEX idx_estacao_id ON leituras(estacao_id, id DESC);

CREATE TABLE leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estacao_id TEXT NOT NULL, recebido_em TEXT NOT NULL,
                luz INTEGER NOT NULL, estado TEXT NOT NULL,
                temperatura REAL, umidade REAL, gas INTEGER,
                pressao REAL, temperatura_bmp REAL, bmp_conectado INTEGER NOT NULL
            );
