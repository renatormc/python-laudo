def rgano(value: str) -> dict:
    try:
        parts = value.split("/")
        return {"rg": int(parts[0]), "ano": int(parts[1])}
    except:
        raise Exception(f"Valor {value} não segue o formato rg/ano")
    