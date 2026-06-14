import requests
import json
import time

def extraer_datos():
    # API Oficial de "Precios en Surtidor" del Gobierno Argentino
    base_url = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    estaciones_dict = {}
    offset = 0
    limit = 2000
    max_retries = 3
    
    print("Iniciando conexión con el nodo de la Secretaría de Energía...")
    
    while True:
        retries = 0
        success = False
        records = []
        
        while retries < max_retries and not success:
            try:
                response = requests.get(f"{base_url}&limit={limit}&offset={offset}", headers=headers, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('result', {}).get('records', [])
                    success = True
                else:
                    retries += 1
                    time.sleep(2)
            except Exception as e:
                print(f"Intento {retries+1} fallido: {e}")
                retries += 1
                time.sleep(2)
        
        if not success or not records:
            break
            
        for r in records:
            bandera = str(r.get('empresabandera', '')).strip().upper()
            nombre = str(r.get('empresa', '')).strip().upper()
            
            # FILTRO EXTREMO: Captura YPF, OPESSA (Subsidiaria YPF) y ACA sin importar los errores de tipeo del Estado.
            es_ypf = 'YPF' in bandera or 'Y.P.F' in bandera or 'YPF' in nombre or 'OPESSA' in nombre
            es_aca = 'ACA' in bandera or 'AUTOMOVIL CLUB' in bandera or 'ACA' in nombre or 'A.C.A' in nombre
            
            if (es_ypf or es_aca) and r.get('latitud') and r.get('longitud'):
                try:
                    # Corrección de formato numérico del gobierno (comas por puntos)
                    lat = float(str(r.get('latitud')).replace(',', '.'))
                    lng = float(str(r.get('longitud')).replace(',', '.'))
                    
                    # Filtro de purga: Elimina coordenadas basura que caen en el océano o en otros países
                    if not (-55.0 <= lat <= -20.0 and -75.0 <= lng <= -50.0):
                        continue
                        
                    id_estacion = f"{lat:.4f}_{lng:.4f}"
                    
                    super_p = float(str(r.get('precio_super', 0)).replace(',', '.'))
                    inf_p = float(str(r.get('precio_infinia', 0)).replace(',', '.'))
                    d500_p = float(str(r.get('precio_gasoil', 0)).replace(',', '.'))
                    infd_p = float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.'))
                    
                    # FLEXIBILIDAD: Guarda la estación si tiene al menos UN combustible cargado (Evita que desaparezcan si les falta 1 precio)
                    if super_p > 100 or inf_p > 100 or d500_p > 100 or infd_p > 100:
                        prefijo = "ACA" if es_aca else "YPF"
                        localidad = str(r.get('idlocalidad', 'NACIONAL')).upper()
                        direccion = str(r.get('direccion', '')).upper()
                        
                        estaciones_dict[id_estacion] = {
                            "name": f"{prefijo} {localidad} - {direccion}",
                            "lat": lat, "lng": lng,
                            "prices": {
                                "Super": super_p, "Infinia": inf_p, "Diesel500": d500_p, "InfiniaDiesel": infd_p
                            }
                        }
                except:
                    pass
                    
        if len(records) < limit:
            break
            
        offset += limit
        print(f"Procesados {offset} registros del bloque nacional...")

    resultado = list(estaciones_dict.values())
    print(f"Mapeo finalizado: {len(resultado)} Estaciones YPF/ACA operativas consolidadas.")
    
    with open('precios.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extraer_datos()
