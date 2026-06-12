import requests
import json
import sys

def extraer_datos():
    # URL oficial optimizada para pedir las estaciones de forma estable
    url_oficial = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82&limit=4000"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    try:
        print("Iniciando conexión con los servidores de la Secretaría de Energía...")
        response = requests.get(url_oficial, headers=headers, timeout=45)
        response.raise_for_status()
        
        # Forzamos la decodificación correcta de caracteres argentinos (acentos, Ñ)
        response.encoding = 'utf-8'
        data = response.json()
        
        registros = data.get('result', {}).get('records', [])
        print(f"Paquete recibido. Procesando {len(registros)} registros nacionales...")
        
        if not registros:
            print("Error: El servidor gubernamental devolvió una base de datos vacía.")
            sys.exit(1)
            
        estaciones_filtradas = []
        
        for r in registros:
            bandera = str(r.get('empresabandera', '')).strip().upper()
            # Filtramos estrictamente YPF / ACA con coordenadas físicas válidas
            if "YPF" in bandera and r.get('latitud') and r.get('longitud'):
                try:
                    localidad = str(r.get('idlocalidad', 'NACIONAL')).strip().upper()
                    direccion = str(r.get('direccion', '')).strip().upper()
                    
                    nodo = {
                        "name": f"YPF {localidad} - {direccion}",
                        "lat": float(str(r.get('latitud')).replace(',', '.').strip()),
                        "lng": float(str(r.get('longitud')).replace(',', '.').strip()),
                        "prices": {
                            "Super": float(str(r.get('precio_super', 0)).replace(',', '.').strip()),
                            "Infinia": float(str(r.get('precio_infinia', 0)).replace(',', '.').strip()),
                            "Diesel500": float(str(r.get('precio_gasoil', 0)).replace(',', '.').strip()),
                            "InfiniaDiesel": float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.').strip())
                        }
                    }
                    
                    # Filtro de control: Evitamos errores de carga o surtidores en $0
                    if nodo["prices"]["Super"] > 500:
                        estaciones_filtradas.append(nodo)
                        
                except (ValueError, TypeError):
                    continue
        
        if len(estaciones_filtradas) == 0:
            print("Error: No se pudieron validar estaciones operativas en este ciclo.")
            sys.exit(1)
            
        # Escritura limpia en disco sin romper caracteres latinos
        with open('precios.json', 'w', encoding='utf-8') as f:
            json.dump(estaciones_filtradas, f, ensure_ascii=False, indent=2)
            
        print(f"Éxito logístico. {len(estaciones_filtradas)} nodos YPF integrados a la telemetría.")
        
    except Exception as e:
        print(f"Falla crítica en el proceso de extracción de red: {e}")
        sys.exit(1)

if __name__ == "__main__":
    extraer_datos()
