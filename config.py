from configparser import ConfigParser

def config(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    if not parser.has_section(section):
        raise Exception(f"Sezione {section} non trovata in {filename}")

    return {key: value for key, value in parser.items(section)}
