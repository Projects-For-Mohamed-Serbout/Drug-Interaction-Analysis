import os
import xml.etree.ElementTree as ET
import json

# XML namespace mapping
NAMESPACES = {
    "atc": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_atc",
    "dcp": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcp",
    "dcpf": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcpf",
    "dcsa": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcsa",
    "envases": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_envases",
    "excipientes": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_excipientes",
    "formasf": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_formas_farmaceuticas",
    "formasfs": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_formas_farmaceuticas_simplificadas",
    "lab": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_laboratorios",
    "principios": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_principios_activos",
    "situacion": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_situacion_registro",
    "unidad": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_unidad_contenido",
    "vias": "http://schemas.aemps.es/prescripcion/aemps_prescripcion_vias_administracion",
    "presc": "http://schemas.aemps.es/prescripcion/aemps_prescripcion",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
}

DATA_DIR = "data"


def parse_generic(filepath, tag, fields, nskey):
    """Generic XML parser for dictionary files"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = {'ns': NAMESPACES[nskey]}
    data = []
    for node in root.findall(f'ns:{tag}', ns):
        entry = {}
        for field in fields:
            child = node.find(f'ns:{field}', ns)
            entry[field] = child.text if child is not None else None
        data.append(entry)
    return data


# Define specific parsing logic for dictionary files
DICTIONARY_PARSERS = {
    "DICCIONARIO_ATC.xml": lambda f: parse_generic(f, "atc", ["nroatc", "codigoatc", "descatc"], "atc"),
    "DICCIONARIO_DCP.xml": lambda f: parse_generic(f, "dcp", ["codigodcp", "nombredcp", "codigodcsa"], "dcp"),
    "DICCIONARIO_DCPF.xml": lambda f: parse_generic(f, "dcpf", ["codigodcpf", "nombredcpf", "codigodcp"], "dcpf"),
    "DICCIONARIO_DCSA.xml": lambda f: parse_generic(f, "dcsa", ["codigodcsa", "nombredcsa"], "dcsa"),
    "DICCIONARIO_ENVASES.xml": lambda f: parse_generic(f, "envases", ["codigoenvase", "envase"], "envases"),
    "DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.xml": lambda f: parse_generic(f, "excipientes", ["codigoedo", "edo"], "excipientes"),
    "DICCIONARIO_FORMA_FARMACEUTICA.xml": lambda f: parse_generic(f, "formasfarmaceuticas", ["codigoformafarmaceutica", "formafarmaceutica", "codigoformafarmaceuticasimplificada"], "formasf"), # noqa
    "DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.xml": lambda f: parse_generic(f, "formasfarmaceuticassimplificadas", ["codigoformafarmaceuticasimplificada", "formafarmaceuticasimplificada"], "formasfs"),# # noqa
    "DICCIONARIO_LABORATORIOS.xml": lambda f: parse_generic(f, "laboratorios", ["codigolaboratorio", "laboratorio", "direccion", "codigopostal", "localidad", "cif"], "lab"),# # noqa
    "DICCIONARIO_PRINCIPIOS_ACTIVOS.xml": lambda f: parse_generic(f, "principiosactivos", ["nroprincipioactivo", "codigoprincipioactivo", "principioactivo"], "principios"),# # noqa
    "DICCIONARIO_SITUACION_REGISTRO.xml": lambda f: parse_generic(f, "situacionesregistro", ["codigosituacionregistro", "situacionregistro"], "situacion"), # # noqa
    "DICCIONARIO_UNIDAD_CONTENIDO.xml": lambda f: parse_generic(f, "unidadescontenido", ["codigounidadcontenido", "unidadcontenido"], "unidad"),
    "DICCIONARIO_VIAS_ADMINISTRACION.xml": lambda f: parse_generic(f, "viasadministracion", ["codigoviaadministracion", "viaadministracion"], "vias"),
}

def parse_prescripcion_xml(file_path):
    """
    Parse Prescripcion.xml file and extract structured prescription data
    """
    ns = {
        'ns': NAMESPACES['presc'],
        'xsi': NAMESPACES['xsi']
    }

    tree = ET.parse(file_path)
    root = tree.getroot()

    def get_text(element, path, default=None):
        """Helper to safely get text from an element or return default"""
        elem = element.find(path, ns)
        return elem.text if elem is not None else default

    # Extract header information
    header = {
        'list_prescription_date': get_text(root, 'ns:header/ns:listprescriptiondate')
    }

    prescriptions = []

    # Process each prescription
    for prescription in root.findall('ns:prescription', ns):
        # Basic prescription info
        presc_data = {
            'cod_nacion': get_text(prescription, 'ns:cod_nacion'),
            'nro_definitivo': get_text(prescription, 'ns:nro_definitivo'),
            'des_nomco': get_text(prescription, 'ns:des_nomco'),
            'des_prese': get_text(prescription, 'ns:des_prese'),
            'cod_dcsa': get_text(prescription, 'ns:cod_dcsa'),
            'cod_dcp': get_text(prescription, 'ns:cod_dcp'),
            'cod_dcpf': get_text(prescription, 'ns:cod_dcpf'),
            'des_dosific': get_text(prescription, 'ns:des_dosific'),
            'cod_envase': get_text(prescription, 'ns:cod_envase'),
            'contenido': get_text(prescription, 'ns:contenido'),
            'unid_contenido': get_text(prescription, 'ns:unid_contenido'),
            'nro_conte': get_text(prescription, 'ns:nro_conte'),
            'sw_psicotropo': get_text(prescription, 'ns:sw_psicotropo'),
            'sw_estupefaciente': get_text(prescription, 'ns:sw_estupefaciente'),
            'sw_afecta_conduccion': get_text(prescription, 'ns:sw_afecta_conduccion'),
            'sw_triangulo_negro': get_text(prescription, 'ns:sw_triangulo_negro'),
            'url_fictec': get_text(prescription, 'ns:url_fictec'),
            'url_prosp': get_text(prescription, 'ns:url_prosp'),
            'sw_receta': get_text(prescription, 'ns:sw_receta'),
            'sw_generico': get_text(prescription, 'ns:sw_generico'),
            'sw_sustituible': get_text(prescription, 'ns:sw_sustituible'),
            'sw_envase_clinico': get_text(prescription, 'ns:sw_envase_clinico'),
            'sw_uso_hospitalario': get_text(prescription, 'ns:sw_uso_hospitalario'),
            'sw_diagnostico_hospitalario': get_text(prescription, 'ns:sw_diagnostico_hospitalario'),
            'sw_tld': get_text(prescription, 'ns:sw_tld'),
            'sw_especial_control_medico': get_text(prescription, 'ns:sw_especial_control_medico'),
            'sw_huerfano': get_text(prescription, 'ns:sw_huerfano'),
            'sw_base_a_plantas': get_text(prescription, 'ns:sw_base_a_plantas'),
            'laboratorio_titular': get_text(prescription, 'ns:laboratorio_titular'),
            'laboratorio_comercializador': get_text(prescription, 'ns:laboratorio_comercializador'),
            'fecha_autorizacion': get_text(prescription, 'ns:fecha_autorizacion'),
            'sw_comercializado': get_text(prescription, 'ns:sw_comercializado'),
            'fec_comer': get_text(prescription, 'ns:fec_comer'),
            'cod_sitreg': get_text(prescription, 'ns:cod_sitreg'),
            'cod_sitreg_presen': get_text(prescription, 'ns:cod_sitreg_presen'),
            'fecha_situacion_registro': get_text(prescription, 'ns:fecha_situacion_registro'),
            'fec_sitreg_presen': get_text(prescription, 'ns:fec_sitreg_presen'),
            'sw_tiene_excipientes_decl_obligatoria': get_text(prescription, 'ns:sw_tiene_excipientes_decl_obligatoria'),
            'biosimilar': get_text(prescription, 'ns:biosimilar'),
            'importacion_paralela': get_text(prescription, 'ns:importacion_paralela'),
            'radiofarmaco': get_text(prescription, 'ns:radiofarmaco'),
            'serializacion': get_text(prescription, 'ns:serializacion'),
        }

        # Pharmaceutical forms
        formas_farma = prescription.find('ns:formasfarmaceuticas', ns)
        if formas_farma is not None:
            presc_data['formas_farmaceuticas'] = {
                'cod_forfar': get_text(formas_farma, 'ns:cod_forfar'),
                'cod_forfar_simplificada': get_text(formas_farma, 'ns:cod_forfar_simplificada'),
                'nro_pactiv': get_text(formas_farma, 'ns:nro_pactiv'),
                'composiciones': [],
                'vias_administracion': []
            }

            # Composition
            for comp in formas_farma.findall('ns:composicion_pa', ns):
                presc_data['formas_farmaceuticas']['composiciones'].append({
                    'cod_principio_activo': get_text(comp, 'ns:cod_principio_activo'),
                    'orden_colacion': get_text(comp, 'ns:orden_colacion'),
                    'dosis_pa': get_text(comp, 'ns:dosis_pa'),
                    'unidad_dosis_pa': get_text(comp, 'ns:unidad_dosis_pa'),
                    'dosis_composicion': get_text(comp, 'ns:dosis_composicion'),
                    'unidad_composicion': get_text(comp, 'ns:unidad_composicion'),
                    'dosis_administracion': get_text(comp, 'ns:dosis_administracion'),
                    'unidad_administracion': get_text(comp, 'ns:unidad_administracion'),
                    'dosis_prescripcion': get_text(comp, 'ns:dosis_prescripcion'),
                    'unidad_prescripcion': get_text(comp, 'ns:unidad_prescripcion')
                })

            # Administration routes
            vias = formas_farma.find('ns:viasadministracion', ns)
            if vias is not None:
                for via in vias.findall('ns:cod_via_admin', ns):
                    if via.text:
                        presc_data['formas_farmaceuticas']['vias_administracion'].append(via.text)

        # ATC codes
        atc = prescription.find('ns:atc', ns)
        if atc is not None:
            presc_data['atc'] = {
                'cod_atc': get_text(atc, 'ns:cod_atc'),
                'duplicidades': []
            }

            for dup in atc.findall('ns:duplicidades', ns):
                presc_data['atc']['duplicidades'].append({
                    'atc_duplicidad': get_text(dup, 'ns:atc_duplicidad'),
                    'descripcion_atc_duplicidad': get_text(dup, 'ns:descripcion_atc_duplicidad'),
                    'efecto_duplicidad': get_text(dup, 'ns:efecto_duplicidad'),
                    'recomendacion_duplicidad': get_text(dup, 'ns:recomendacion_duplicidad')
                })
        # Supply problems
        problemas = prescription.find('ns:problemassuministro', ns)
        if problemas is not None:
            presc_data['problemas_suministro'] = {
                'fecha_inicio': get_text(problemas, 'ns:fecha_inicio'),
                'observaciones': get_text(problemas, 'ns:observaciones')
            }

        prescriptions.append(presc_data)

    return {
        'header': header,
        'prescriptions': prescriptions
    }


def run_dictionary_parsers(data_dir):
    """Run all dictionary parsers and return combined results as a dictionary"""
    dictionary_data = {}
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if not filename.endswith(".xml") or filename.lower() == "prescripcion.xml":
            continue

        parser_fn = DICTIONARY_PARSERS.get(filename)
        if parser_fn:
            try:
                parsed_data = parser_fn(filepath)
                dictionary_data[filename.replace(".xml", "").lower()] = parsed_data
            except Exception as e:
                print(f"❌ Error parsing {filename}: {e}")
        else:
            print(f"⚠️ No parser defined for {filename}, skipping.")
    return dictionary_data


def main():
    """Main function to run both dictionary and prescription parsing"""
    # Run dictionary parsers
    dictionary_data = run_dictionary_parsers()

    # Parse prescription file if it exists
    prescription_file = os.path.join(DATA_DIR, "Prescripcion.xml")
    if os.path.exists(prescription_file):
        print("\n📄 Parsing prescription file...")
        try:
            prescription_data = parse_prescripcion_xml(prescription_file)
            print(f"✅ Parsed {len(prescription_data['prescriptions'])} prescriptions")

            # Save to JSON files
            with open('dictionaries.json', 'w', encoding='utf-8') as f:
                json.dump(dictionary_data, f, ensure_ascii=False, indent=2)

            with open('prescriptions.json', 'w', encoding='utf-8') as f:
                json.dump(prescription_data, f, ensure_ascii=False, indent=2)

            print("\nData successfully saved to dictionaries.json and prescriptions.json")
        except Exception as e:
            print(f"❌ Error parsing prescription file: {e}")
    else:
        print("\n⚠️ Prescripcion.xml not found in data directory, skipping prescription parsing")


def extract_all(data_dir):
    """
    Extract dictionaries and prescriptions from XML files in the given directory.
    Returns a tuple:
        (dictionary_data: dict[str, list[dict]],
         prescription_data: dict[str, Any] | None)
    """
    dictionaries = run_dictionary_parsers(data_dir)
    prescription_path = os.path.join(data_dir, "Prescripcion.xml")
    prescriptions = parse_prescripcion_xml(prescription_path) if os.path.exists(prescription_path) else None
    return dictionaries, prescriptions
