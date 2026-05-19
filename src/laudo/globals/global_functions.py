import itertools
import os


class GlobalFunctions:

    def len(self, value):
        return len(value)

    def to_table(self, value, per_row):
        return [value[i * per_row:(i + 1) * per_row] for i in range((len(value) + per_row - 1) // per_row)]

    def remove_nulls(self, items, attrib):
        res = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, dict):
                if item[attrib] is not None:
                    res.append(item)
                continue
            if getattr(item, attrib) is not None:
                res.append(item)
        return res

    def male_female(self, data, male_option, female_option):
        try:
            if data['gender'] == 'M':
                return male_option
            else:
                return female_option
        except:
            return male_option

    def gender(self, data, male_value):
        if data['gender'] == 'F':
            if male_value.endswith('o'):
                return f"{male_value[:-1]}a"
            return f"{male_value}a"
        return male_value

    def plural(self, value, n):
        if n > 1:
            return f"{value}s"
        return value

    def not_null_or(self, value, default):
        if not value:
            return default
        return value

    def ifplural(self, value, plural, singular=""):
        """Verifica se uma lista possui mais de um elemento e retorna um valor plural ou singular"""
        if isinstance(value, list):
            return plural if len(value) > 1 else singular
        return plural if value > 1 else singular

    def count_qtd(self, value, field=None):
        qtd = 0
        for item in value:
            if isinstance(item, dict):
                qtd += item[field]
            elif isinstance(item, int):
                qtd += item
        return qtd

    def case_(self, var, options):
        if var in options.keys():
            return options[var]
        if 'default' in options.keys():
            return options['default']

    def get_paragraphs(self, value):
        return [line.strip() for line in value.split("\n")]

    def join_path(self, *args):
        return os.path.join(*args)

    def join_lists(self, *args):
        return itertools.chain(*args)

    def aa(self, value, name):
        return value

    def caption(self, label: str, ref: str, caption: str) -> str:
        aux = f" - {caption}" if caption else ""
        return "${" + f"{label}|{ref}" + "}" + aux
    
    def str_list(self, *args: str, separator=", "):
        ret = []
        for value in args:
            value = str(value).strip()
            if value:
                ret.extend(value.split(separator))
        return ret
        
    

