import requests
import json

def extraer_datos():
    base_url = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    # El diccionario evitará estaciones duplicadas y retendrá siempre la actualización de precio más reciente
    estaciones_dict = {}
    offset = 0
    limit = 5000
    
    try:
        print("Iniciando barrido profundo (Deep Scan) de toda la República Argentina...")
        
        while True:
            print(f"Extrayendo bloque operativo: Registros {offset} a {offset + limit}...")
            
            response = requests.get(f"{base_url}&limit={limit}&offset={offset}", headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            data = response.json()
            
            records = data.get('result', {}).get('records', [])
            
            # Si el bloque viene vacío, significa que mapeamos todo el país
            if not records:
                break 
                
            for r in records:
                bandera = str(r.get('empresabandera', '')).strip().upper()
                if "YPF" in bandera and r.get('latitud') and r.get('longitud'):
                    try:
                        # Generamos un ID topográfico único
                        lat = float(str(r.get('latitud')).replace(',', '.'))
                        lng = float(str(r.get('longitud')).replace(',', '.'))
                        id_estacion = f"{lat:.4f}_{lng:.4f}"
                        
                        localidad = str(r.get('idlocalidad', 'NACIONAL')).upper()
                        direccion = str(r.get('direccion', '')).upper()
                        
                        super_precio = float(str(r.get('precio_super', 0)).replace(',', '.'))
                        
                        # Filtro de seguridad para evitar precios en cero por errores del Ministerio
                        if super_precio > 500:
                            # Al usar el ID como clave, si el Estado cargó 2 precios para la misma YPF,
                            # el sistema siempre conservará el último (el actualizado).
                            estaciones_dict[id_estacion] = {
                                "name": f"YPF {localidad} - {direccion}",
                                "lat": lat,
                                "lng": lng,
                                "prices": {
                                    "Super": super_precio,
                                    "Infinia": float(str(r.get('precio_infinia', 0)).replace(',', '.')),
                                    "Diesel500": float(str(r.get('precio_gasoil', 0)).replace(',', '.')),
                                    "InfiniaDiesel": float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.'))
                                }
                            }
                    except:
                        continue
                        
            # Si trajo menos de 5000, es la última página de la base de datos oficial
            if len(records) < limit:
                break
                
            offset += limit
            
        estaciones_filtradas = list(estaciones_dict.values())
        print(f"Barrido completado: {len(estaciones_filtradas)} estaciones YPF únicas consolidadas.")
        
    except Exception as e:
        print(f"Error de red durante el rastreo masivo: {e}")
        estaciones_filtradas = []

    # FAIL-SAFE: Solo se activa si la red del Estado sufre una caída total
    if len(estaciones_filtradas) < 50:
        print("Protocolo de emergencia: Inyectando memoria de contingencia.")
        estaciones_filtradas = [
            {"name": "YPF ACA CABA (CONTINGENCIA)", "lat": -34.5805, "lng": -58.4065, "prices": {"Super": 1184, "Infinia": 1403, "Diesel500": 1190, "InfiniaDiesel": 1374}},
            {"name": "YPF RN11 FORMOSA (CONTINGENCIA)", "lat": -26.1848, "lng": -58.1731, "prices": {"Super": 1349, "Infinia": 1577, "Diesel500": 1373, "InfiniaDiesel": 1543}}
        ]

    # Guardado seguro
    with open('precios.json', 'w', encoding='utf-8') as f:
        json.dump(estaciones_filtradas, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extraer_datos()
