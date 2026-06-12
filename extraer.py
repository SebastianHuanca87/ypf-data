import requests
import json
import os

def extraer_datos():
    url_oficial = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82&limit=4000"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    estaciones_filtradas = []
    
    try:
        print("Iniciando reconocimiento en servidores de la Secretaría de Energía...")
        # El timeout corto evita que el script se quede colgado si el gobierno bloquea la IP
        response = requests.get(url_oficial, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        data = response.json()
        
        registros = data.get('result', {}).get('records', [])
        
        for r in registros:
            bandera = str(r.get('empresabandera', '')).strip().upper()
            if "YPF" in bandera and r.get('latitud') and r.get('longitud'):
                try:
                    nodo = {
                        "name": f"YPF {str(r.get('idlocalidad', 'NACIONAL')).upper()}",
                        "lat": float(str(r.get('latitud')).replace(',', '.')),
                        "lng": float(str(r.get('longitud')).replace(',', '.')),
                        "prices": {
                            "Super": float(str(r.get('precio_super', 0)).replace(',', '.')),
                            "Infinia": float(str(r.get('precio_infinia', 0)).replace(',', '.')),
                            "Diesel500": float(str(r.get('precio_gasoil', 0)).replace(',', '.')),
                            "InfiniaDiesel": float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.'))
                        }
                    }
                    if nodo["prices"]["Super"] > 500:
                        estaciones_filtradas.append(nodo)
                except:
                    continue

    except Exception as e:
        print(f"Alerta: Conexión gubernamental rechazada o inestable ({e}).")
    
    # FAIL-SAFE: Si hay bloqueo, el sistema no colapsa, inyecta datos de contingencia
    if len(estaciones_filtradas) == 0:
        print("Activando inyección de base de datos de contingencia (Offline Protocol)...")
        estaciones_filtradas = [
            {"name": "YPF ACA CABA (CONTINGENCIA)", "lat": -34.5805, "lng": -58.4065, "prices": {"Super": 1184, "Infinia": 1403, "Diesel500": 1190, "InfiniaDiesel": 1374}},
            {"name": "YPF RN11 FORMOSA (CONTINGENCIA)", "lat": -26.1848, "lng": -58.1731, "prices": {"Super": 1349, "Infinia": 1577, "Diesel500": 1373, "InfiniaDiesel": 1543}},
            {"name": "YPF RN9 ROSARIO (CONTINGENCIA)", "lat": -32.9511, "lng": -60.6664, "prices": {"Super": 1210, "Infinia": 1450, "Diesel500": 1235, "InfiniaDiesel": 1465}}
        ]

    # Guardado seguro: Garantiza que el archivo exista siempre para tu HTML
    with open('precios.json', 'w', encoding='utf-8') as f:
        json.dump(estaciones_filtradas, f, ensure_ascii=False, indent=2)
    
    print("Exportación JSON completada con éxito.")

if __name__ == "__main__":
    extraer_datos()
