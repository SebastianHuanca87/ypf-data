import requests
import json

def extraer_datos():
    # URL del recurso oficial de la Secretaría de Energía (Precios en Surtidor)
    url_oficial = "https://datos.minem.gob.ar/api/3/action/datastore_search?resource_id=d2b2ece0-a46f-40ec-94a6-427771744b82&limit=5000"
    
    try:
        print("Iniciando extracción de datos desde el servidor nacional...")
        response = requests.get(url_oficial, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        registros = data.get('result', {}).get('records', [])
        estaciones_filtradas = []
        
        for r in registros:
            # Filtramos estrictamente por bandera YPF y nos aseguramos de que tengan coordenadas válidas
            bandera = str(r.get('empresabandera', '')).strip().upper()
            if "YPF" in bandera and r.get('latitud') and r.get('longitud'):
                try:
                    # Estructura exacta que requiere el motor de telemetría de tu HTML
                    nodo = {
                        "name": f"YPF {str(r.get('idlocalidad', 'NACIONAL')).upper()} - {str(r.get('direccion', '')).upper()}",
                        "lat": float(str(r.get('latitud')).replace(',', '.')),
                        "lng": float(str(r.get('longitud')).replace(',', '.')),
                        "prices": {
                            "Super": float(str(r.get('precio_super', 0)).replace(',', '.')),
                            "Infinia": float(str(r.get('precio_infinia', 0)).replace(',', '.')),
                            "Diesel500": float(str(r.get('precio_gasoil', 0)).replace(',', '.')),
                            "InfiniaDiesel": float(str(r.get('precio_gasoil_premium', 0)).replace(',', '.'))
                        }
                    }
                    # Evitamos incluir nodos con precios en cero por errores de carga del estacionero
                    if nodo["prices"]["Super"] > 100:
                        estaciones_filtradas.append(nodo)
                except (ValueError, TypeError):
                    continue # Si hay un dato corrupto, el subagente lo salta para no romper la base
        
        # Guardamos la base de datos limpia
        with open('precios.json', 'w', encoding='utf-8') as f:
            json.dump(estaciones_filtradas, f, ensure_ascii=False, indent=2)
            
        print(f"Sincronización exitosa. {len(estaciones_filtradas)} estaciones YPF validadas.")
        
    except Exception as e:
        print(f"Error crítico en la extracción: {e}")
        exit(1)

if __name__ == "__main__":
    extraer_datos()
