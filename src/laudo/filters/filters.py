from datetime import date, datetime
from .helpers_filters import *
import math
from pathlib import Path


nome_meses = [
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro'
]


class Filters:

    def rgano(self, value: str) -> dict:
        try:
            parts = value.split("/")
            return {"rg": int(parts[0]), "ano": int(parts[1])}
        except:
            raise Exception(f"Valor {value} não segue o formato rg/ano")

    def perano(self, value: str) -> int:
        return self.rgano(value)['ano']

    def perrg(self, value: str) -> int:
        return self.rgano(value)['rg']

    def br(self, value, loop_):
        return value if loop_.index == 1 else f"<w:br/>{value}"

    def not_null(self, value):
        if value is None:
            return ""
        return value

    def xxx(self, value):
        if value is None:
            return "XXX"
        return value

    def data_completa(self, value):
        if not isinstance(value, datetime) and not isinstance(value, date):
            return ""
        dia = str(value.day).rjust(2, "0")
        dia_extenso = get_extenso(value.day)
        return f"{dia} ({dia_extenso}) dias do mês de {nome_meses[value.month - 1]} do ano de {value.year} ({get_extenso(value.year)})"

    def data_mes_extenso(self, value):
        if not isinstance(value, datetime) and not isinstance(value, date):
            return ""
        value = convert_datetime(value)
        dia = str(value.day) if value.day > 1 else f"{value.day}°"
        return f"{dia} de {nome_meses[value.month - 1]} de {value.year}"

    def hora_minuto(self, value):
        if not isinstance(value, datetime):
            return "XXX"
        value = convert_datetime(value)
        hora = str(value.hour).rjust(2, "0")
        minuto = str(value.minute).rjust(2, "0")
        return f"{hora}:{minuto}"

    def dia(self, value):
        if not isinstance(value, datetime):
            return "XXX"
        value = convert_datetime(value)
        return str(value.day).rjust(2, "0")

    def dia_extenso(self, value):
        if not isinstance(value, datetime):
            return "XXX"
        value = convert_datetime(value)
        dia = str(value.day).rjust(2, "0")
        dia_extenso = get_extenso(value.day)
        return f"{dia} ({dia_extenso})"

    def numero_extenso_masc(self, value):
        return get_extenso(value)

    def numero_extenso_fem(self, value):
        return get_extenso(value, feminino=True)

    def mes_extenso(self, value):
        if not isinstance(value, datetime):
            return "XXX"
        return nome_meses[value.month-1]

    def data_simples(self, value):
        if not value:
            return ""
        value = convert_datetime(value)
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")
        try:
            data = datetime.strptime(value, "%d/%m/%Y")
            return data.strftime("%d/%m/%Y")
        except Exception as e:
            print(e)
            pass

    def is_male(self, value):
        if isinstance(value, str):
            firstname = value.split()[0]
            return firstname.endswith('o')
        return False

    def get_extenso(self, value, feminino=False):
        return get_extenso(value, feminino=feminino)

    def datetime(self, value):
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except:
            pass

    def join_enumerate(self, values, with_quotes=False):
        n = len(values)
        if n == 0 :
            return ""
        if n == 1:
            return str(values[0])
        if with_quotes:
            values = [f"\"{v}\"" for v in values]
        else:
            values = [str(v) for v in values]
        parts1 = values[:-1]
        text1 = ", ".join(parts1)
        return f"{text1} e {values[-1]}"

    def moeda_extenso(self, value, prefix="R$ "):
        value_str = f"{value:.2f}".replace(".", ",")
        reais = math.floor(value)
        centavos = int((value%reais + 0.0000000001)*100) if reais > 0 else value*100
        reais_text = get_extenso(reais)
        aux1 = "reais" if reais > 1 else "real"
        aux2 = "centavos" if centavos > 1 else "centavo"
        centavos_text = get_extenso(centavos)

        middle_text = f"{reais_text} {aux1}"
        if centavos > 0:
            middle_text += f" e {centavos_text} {aux2}"
        text = f"{prefix}{value_str} ({middle_text})"
        return text

    def file_stem(self, value):
        try:
            path = Path(value)
            return path.stem
        except:
            return ""


    def str(self, value):
        return str(value)

    def bookmark(self, value, anyvalue):
        return value

    def ornow(self, value):
        if not value:
            return datetime.now()
        return value
