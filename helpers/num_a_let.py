def _entero_a_letras(n):
        """
        Convierte la parte entera (n >= 0) a letras en español.
        Maneja hasta millones. No agrega 'PESOS' ni maneja decimales aquí.
        """
        if n == 0:
            return "cero"

        unidades = [
            "cero", "uno", "dos", "tres", "cuatro",
            "cinco", "seis", "siete", "ocho", "nueve"
        ]
        especiales_10_19 = {
            10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
            15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve"
        }
        decenas = {
            20: "veinte", 30: "treinta", 40: "cuarenta", 50: "cincuenta",
            60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"
        }
        centenas = {
            100: "cien", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
            500: "quinientos", 600: "seiscientos", 700: "setecientos",
            800: "ochocientos", 900: "novecientos"
        }

        def centenas_a_letras(num):
            """Convierte un número de 1 a 999 en letras."""
            if num == 0:
                return ""
            elif num <= 9:
                return unidades[num]
            elif 10 <= num <= 19:
                return especiales_10_19[num]
            elif 20 <= num <= 29:
                if num == 20:
                    return "veinte"
                else:
                    return "veinti" + unidades[num - 20]
            elif 30 <= num <= 99:
                dec = (num // 10) * 10
                uni = num % 10
                if uni == 0:
                    return decenas[dec]
                else:
                    return decenas[dec] + " y " + unidades[uni]
            else:
                # 100 a 999
                cen = (num // 100) * 100
                resto = num % 100
                if cen == 100:
                    if resto == 0:
                        return "cien"
                    else:
                        return "ciento " + centenas_a_letras(resto)
                else:
                    texto_cen = centenas[cen]
                    if resto == 0:
                        return texto_cen
                    else:
                        return texto_cen + " " + centenas_a_letras(resto)

        resultado = ""
        millones = n // 1_000_000
        resto_millones = n % 1_000_000

        if millones > 0:
            if millones == 1:
                resultado += "un millón"
            else:
                resultado += centenas_a_letras(millones) + " millones"
            if resto_millones > 0:
                resultado += " "

        miles = resto_millones // 1000
        resto_miles = resto_millones % 1000

        if miles > 0:
            if miles == 1:
                resultado += "mil"
            else:
                resultado += centenas_a_letras(miles) + " mil"
            if resto_miles > 0:
                resultado += " "

        if resto_miles > 0:
            resultado += centenas_a_letras(resto_miles)

        return resultado.strip()    

def numero_a_letras(numero):
        """
        Convierte 'numero' a su representación en letras en español y 
        finaliza con la palabra 'PESOS', todo en mayúsculas.
        Maneja hasta millones, parte decimal (2 dígitos) y números negativos.
        """
        if numero == 0:
            return "CERO PESOS"

        # Detectar si es negativo
        negativo = False
        if numero < 0:
            negativo = True
            numero = abs(numero)

        # Separar parte entera y decimal (máximo 2 dígitos)
        parte_entera = int(numero)
        parte_decimal = round((numero - parte_entera) * 100)

        # Convertir parte entera a letras
        letras_entero = _entero_a_letras(parte_entera)

        # Si hay decimales, se convierten a letras y se unen con "con"
        if parte_decimal > 0:
            letras_decimal = _entero_a_letras(parte_decimal)
            resultado = f"{letras_entero} CON {letras_decimal} PESOS"
        else:
            resultado = f"{letras_entero} PESOS"

        if negativo:
            resultado = f"MENOS {resultado}"

        return resultado.upper()