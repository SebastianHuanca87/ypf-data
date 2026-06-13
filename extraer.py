import requests
import json

def extraer_datos():
    base_url = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82"
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    
    estaciones_dict = {}
    offset = 0
    limit = 5000
    
    try:
        print("Iniciando barrido de Espectro Amplio (YPF + ACA)...")
        while True:
            response = requests.get(f"{base_url}&limit={limit}&offset={offset}", headers=headers, timeout=30)
            records = response.json().get('result', {}).get('records', [])
            if not records: break 
                
            for r in records:
                bandera = str(r.get('empresabandera', '')).strip().upper()
                nombre = str(r.get('empresa', '')).strip().upper()
                
                # FIX: Captura YPF, ACA y Automóvil Club Argentino sin importar cómo lo haya escrito el Estado
                es_ypf_o_aca = ("YPF" in bandera or "ACA" in bandera or "AUTOMOVIL CLUB" in bandera or "YPF" in nombre or "ACA" in nombre)
                
                if es_ypf_o_aca and r.get('latitud') and r.get('longitud'):
                    try:
                        lat = float(str(r.get('latitud')).replace(',', '.'))
                        lng = float(str(r.get('longitud')).replace(',', '.'))
                        id_estacion = f"{lat:.4f}_{lng:.4f}"
                        
                        localidad = str(r.get('idlocalidad', 'NACIONAL')).upper()
                        direccion = str(r.get('direccion', '')).upper()
                        
                        super_p = float(str(r.get('precio_super', 0)).replace(',', '.'))
                        diesel_p = float(str(r.get('precio_gasoil', 0)).replace(',', '.'))
                        
                        # Flexibilizamos el filtro para que guarde la estación si tiene AL MENOS un combustible registrado
                        if super_p > 100 or diesel_p > 100:
                            prefijo = "ACA" if ("ACA" in bandera or "AUTOMOVIL" in bandera or "ACA" in nombre) else "YPF"
                            estaciones_dict[id_estacion] = {
                                "name": f"{prefijo} {localidad} - {direccion}",
                                "lat": lat, "lng": lng,
                                "prices": {
                                    "Super": super_p,
                                    "Infinia": float(str(r.get('precio_infinia', 0)).replace(',', '.')),
                                    "Diesel500": diesel_p,
                                    "InfiniaDiesel": float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.'))
                                }
                            }
                    except: continue
            if len(records) < limit: break
            offset += limit
            
        estaciones_filtradas = list(estaciones_dict.values())
        print(f"Barrido completado: {len(estaciones_filtradas)} estaciones consolidadas.")
        
    except Exception as e:
        print(f"Error: {e}")
        estaciones_filtradas = []

    if len(estaciones_filtradas) < 50:
        estaciones_filtradas = [{"name": "YPF CONTINGENCIA", "lat": -34.5, "lng": -58.4, "prices": {"Super": 1000, "Infinia": 1200, "Diesel500": 1050, "InfiniaDiesel": 1250}}]

    with open('precios.json', 'w', encoding='utf-8') as f:
        json.dump(estaciones_filtradas, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extraer_datos()
