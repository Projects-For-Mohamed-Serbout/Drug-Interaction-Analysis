# python -m app.extractor.convert_xml_csv

import xml.etree.ElementTree as ET
import csv
import os
import sys
import argparse


class XMLToCSVConverter:
    """
    A unified converter for processing multiple XML files and converting them to CSV format.
    All XML files are expected to be in the same input directory, and all CSV files will be
    written to the same output directory.
    """

    def __init__(self, input_dir='data', output_dir='data/csv'):
        """
        Initialize the converter with input and output directories.

        Args:
            input_dir (str): Directory containing XML files
            output_dir (str): Directory where CSV files will be saved
        """
        self.input_dir = input_dir
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Namespace mappings for each XML file type
        self.namespaces = {
            'ATC': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_atc'},
            'DCP': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcp'},
            'DCPF': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcpf'},
            'DCSA': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_dcsa'},
            'ENVASES': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_envases'},
            'EXCIPIENTES': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_excipientes'},
            'FORMA_FARMACEUTICA_SIMPLIFICADAS': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_formas_farmaceuticas_simplificadas'},
            'FORMA_FARMACEUTICA': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_formas_farmaceuticas'},
            'LABORATORIOS': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_laboratorios'},
            'UNIDAD_CONTENIDO': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_unidad_contenido'},
            'VIAS_ADMINISTRACION': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_vias_administracion'},
            'PRINCIPIOS_ACTIVOS': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_principios_activos'},
            'SITUACION_REGISTRO': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion_situacion_registro'},
            'PRESCRIPCION': {'ns': 'http://schemas.aemps.es/prescripcion/aemps_prescripcion'},
        }

    def get_text_or_default(self, parent, tag, namespace, default=''):
        """
        Helper method to safely get text from an XML element or return a default value.

        Args:
            parent: The parent XML element
            tag: The tag to find within the parent
            namespace: The namespace dictionary to use
            default: The default value to return if element is not found or has no text

        Returns:
            The text content of the element or the default value
        """
        el = parent.find(tag, namespace)
        return el.text.strip() if el is not None and el.text else default

    def process_atc(self):
        """Process ATC XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_ATC.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_ATC.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['ATC']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['nroatc', 'codigoatc', 'descatc'])  # header

            for atc in root.findall('ns:atc', ns):
                nroatc = atc.find('ns:nroatc', ns).text
                codigoatc = atc.find('ns:codigoatc', ns).text
                descatc = atc.find('ns:descatc', ns).text
                writer.writerow([nroatc, codigoatc, descatc])

        return output_file

    def process_dcp(self):
        """Process DCP XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_DCP.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_DCP.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['DCP']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigodcp', 'nombredcp', 'codigodcsa'])

            for dcp in root.findall('ns:dcp', ns):
                codigodcp = dcp.find('ns:codigodcp', ns).text
                nombredcp = dcp.find('ns:nombredcp', ns).text
                codigodcsa = dcp.find('ns:codigodcsa', ns).text
                writer.writerow([codigodcp, nombredcp, codigodcsa])

        return output_file

    def process_dcpf(self):
        """Process DCPF XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_DCPF.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_DCPF.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['DCPF']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigodcpf', 'nombredcpf', 'codigodcp'])

            for dcpf in root.findall('ns:dcpf', ns):
                codigodcpf = dcpf.find('ns:codigodcpf', ns).text
                nombredcpf = dcpf.find('ns:nombredcpf', ns).text
                codigodcp = dcpf.find('ns:codigodcp', ns).text
                writer.writerow([codigodcpf, nombredcpf, codigodcp])

        return output_file

    def process_dcsa(self):
        """Process DCSA XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_DCSA.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_DCSA.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['DCSA']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigodcsa', 'nombredcsa'])

            for dcsa in root.findall('ns:dcsa', ns):
                codigodcsa = dcsa.find('ns:codigodcsa', ns).text
                nombredcsa = dcsa.find('ns:nombredcsa', ns).text
                writer.writerow([codigodcsa, nombredcsa])

        return output_file

    def process_envases(self):
        """Process ENVASES XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_ENVASES.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_ENVASES.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['ENVASES']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigoenvase', 'envase'])

            for envase in root.findall('ns:envases', ns):
                codigoenvase = envase.find('ns:codigoenvase', ns).text
                envase_text = envase.find('ns:envase', ns).text
                writer.writerow([codigoenvase, envase_text])

        return output_file

    def process_excipientes(self):
        """Process EXCIPIENTES XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['EXCIPIENTES']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigoedo', 'edo'])

            for excipiente in root.findall('ns:excipientes', ns):
                codigoedo = excipiente.find('ns:codigoedo', ns).text
                edo = excipiente.find('ns:edo', ns).text
                writer.writerow([codigoedo, edo])

        return output_file

    def process_forma_farmaceutica_simplificadas(self):
        """Process FORMA_FARMACEUTICA_SIMPLIFICADAS XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['FORMA_FARMACEUTICA_SIMPLIFICADAS']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigoformafarmaceuticasimplificada', 'formafarmaceuticasimplificada'])

            for item in root.findall('ns:formasfarmaceuticassimplificadas', ns):
                codigo = item.find('ns:codigoformafarmaceuticasimplificada', ns).text
                nombre = item.find('ns:formafarmaceuticasimplificada', ns).text
                writer.writerow([codigo, nombre])

        return output_file

    def process_forma_farmaceutica(self):
        """Process FORMA_FARMACEUTICA XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_FORMA_FARMACEUTICA.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_FORMA_FARMACEUTICA.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['FORMA_FARMACEUTICA']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigoformafarmaceutica', 'formafarmaceutica', 'codigoformafarmaceuticasimplificada'])

            for item in root.findall('ns:formasfarmaceuticas', ns):
                codigo = item.find('ns:codigoformafarmaceutica', ns).text
                nombre = item.find('ns:formafarmaceutica', ns).text
                simplificado = item.find('ns:codigoformafarmaceuticasimplificada', ns).text
                writer.writerow([codigo, nombre, simplificado])

        return output_file

    def process_laboratorios(self):
        """Process LABORATORIOS XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_LABORATORIOS.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_LABORATORIOS.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['LABORATORIOS']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigolaboratorio', 'laboratorio', 'direccion', 'codigopostal', 'localidad', 'cif'])

            for lab in root.findall('ns:laboratorios', ns):
                cod = self.get_text_or_default(lab, 'ns:codigolaboratorio', ns)
                nombre = self.get_text_or_default(lab, 'ns:laboratorio', ns)
                direccion = self.get_text_or_default(lab, 'ns:direccion', ns)
                postal = self.get_text_or_default(lab, 'ns:codigopostal', ns)
                localidad = self.get_text_or_default(lab, 'ns:localidad', ns)
                cif = self.get_text_or_default(lab, 'ns:cif', ns)
                writer.writerow([cod, nombre, direccion, postal, localidad, cif])

        return output_file

    def process_unidad_contenido(self):
        """Process UNIDAD_CONTENIDO XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_UNIDAD_CONTENIDO.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_UNIDAD_CONTENIDO.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['UNIDAD_CONTENIDO']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigounidadcontenido', 'unidadcontenido'])

            for item in root.findall('ns:unidadescontenido', ns):
                codigo = item.find('ns:codigounidadcontenido', ns).text
                nombre = item.find('ns:unidadcontenido', ns).text
                writer.writerow([codigo, nombre])

        return output_file

    def process_vias_administracion(self):
        """Process VIAS_ADMINISTRACION XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_VIAS_ADMINISTRACION.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_VIAS_ADMINISTRACION.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['VIAS_ADMINISTRACION']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigoviaadministracion', 'viaadministracion'])

            for item in root.findall('ns:viasadministracion', ns):
                codigo = item.find('ns:codigoviaadministracion', ns).text
                nombre = item.find('ns:viaadministracion', ns).text
                writer.writerow([codigo, nombre])

        return output_file

    def process_principios_activos(self):
        """Process PRINCIPIOS_ACTIVOS XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_PRINCIPIOS_ACTIVOS.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_PRINCIPIOS_ACTIVOS.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['PRINCIPIOS_ACTIVOS']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['nroprincipioactivo', 'codigoprincipioactivo', 'principioactivo'])

            for pa in root.findall('ns:principiosactivos', ns):
                nro = pa.find('ns:nroprincipioactivo', ns).text
                codigo = pa.find('ns:codigoprincipioactivo', ns).text
                nombre = pa.find('ns:principioactivo', ns).text
                writer.writerow([nro, codigo, nombre])

        return output_file

    def process_situacion_registro(self):
        """Process SITUACION_REGISTRO XML file and convert to CSV"""
        input_file = os.path.join(self.input_dir, 'DICCIONARIO_SITUACION_REGISTRO.xml')
        output_file = os.path.join(self.output_dir, 'DICCIONARIO_SITUACION_REGISTRO.csv')

        tree = ET.parse(input_file)
        root = tree.getroot()
        ns = self.namespaces['SITUACION_REGISTRO']

        with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['codigosituacionregistro', 'situacionregistro'])

            for item in root.findall('ns:situacionesregistro', ns):
                codigo = item.find('ns:codigosituacionregistro', ns).text
                nombre = item.find('ns:situacionregistro', ns).text
                writer.writerow([codigo, nombre])

        return output_file

    def process_prescripcion(self):
        """Process the main Prescripcion XML file and convert to multiple related CSVs"""
        input_file = os.path.join(self.input_dir, 'Prescripcion.xml')
        results = {}

        try:
            # Parse the XML file
            tree = ET.parse(input_file)
            root = tree.getroot()
            ns = self.namespaces['PRESCRIPCION']

            # ------------------- Main PRESCRIPCION.csv -------------------
            main_output_file = os.path.join(self.output_dir, 'PRESCRIPCION.csv')
            with open(main_output_file, mode='w', newline='', encoding='utf-8') as f_main:
                main_writer = csv.writer(f_main)
                main_writer.writerow([
                    'cod_nacion', 'nro_definitivo', 'des_nomco', 'cod_dcp', 'cod_dcpf',
                    'cod_dcsa', 'cod_envase', 'contenido', 'unid_contenido', 'laboratorio_titular',
                    'fecha_autorizacion', 'cod_sitreg', 'sw_generico', 'url_fictec'
                ])

                for pres in root.findall('ns:prescription', ns):
                    main_writer.writerow([
                        pres.findtext('ns:cod_nacion', '', ns),
                        pres.findtext('ns:nro_definitivo', '', ns),
                        pres.findtext('ns:des_nomco', '', ns),
                        pres.findtext('ns:cod_dcp', '', ns),
                        pres.findtext('ns:cod_dcpf', '', ns),
                        pres.findtext('ns:cod_dcsa', '', ns),
                        pres.findtext('ns:cod_envase', '', ns),
                        pres.findtext('ns:contenido', '', ns),
                        pres.findtext('ns:unid_contenido', '', ns),
                        pres.findtext('ns:laboratorio_titular', '', ns),
                        pres.findtext('ns:fecha_autorizacion', '', ns),
                        pres.findtext('ns:cod_sitreg', '', ns),
                        pres.findtext('ns:sw_generico', '', ns),
                        pres.findtext('ns:url_fictec', '', ns),
                    ])

            results['PRESCRIPCION'] = f"CSV file created successfully: {main_output_file}"
            print(results['PRESCRIPCION'])

            # ------------------- Composition: PRESCRIPCION_COMPOSICION.csv -------------------
            comp_output_file = os.path.join(self.output_dir, 'PRESCRIPCION_COMPOSICION.csv')
            with open(comp_output_file, mode='w', newline='', encoding='utf-8') as f_comp:
                comp_writer = csv.writer(f_comp)
                comp_writer.writerow([
                    'nro_definitivo', 'cod_principio_activo', 'orden_colacion', 'dosis_pa',
                    'unidad_dosis_pa', 'dosis_composicion', 'unidad_composicion',
                    'dosis_administracion', 'unidad_administracion', 'dosis_prescripcion',
                    'unidad_prescripcion'
                ])

                for pres in root.findall('ns:prescription', ns):
                    nro_def = pres.findtext('ns:nro_definitivo', '', ns)
                    formas = pres.find('ns:formasfarmaceuticas', ns)
                    if formas is not None:
                        for comp in formas.findall('ns:composicion_pa', ns):
                            comp_writer.writerow([
                                nro_def,
                                comp.findtext('ns:cod_principio_activo', '', ns),
                                comp.findtext('ns:orden_colacion', '', ns),
                                comp.findtext('ns:dosis_pa', '', ns),
                                comp.findtext('ns:unidad_dosis_pa', '', ns),
                                comp.findtext('ns:dosis_composicion', '', ns),
                                comp.findtext('ns:unidad_composicion', '', ns),
                                comp.findtext('ns:dosis_administracion', '', ns),
                                comp.findtext('ns:unidad_administracion', '', ns),
                                comp.findtext('ns:dosis_prescripcion', '', ns),
                                comp.findtext('ns:unidad_prescripcion', '', ns),
                            ])

            results['PRESCRIPCION_COMPOSICION'] = f"CSV file created successfully: {comp_output_file}"
            print(results['PRESCRIPCION_COMPOSICION'])

            # ------------------- ATC Duplicidades: PRESCRIPCION_ATC_DUPLICIDADES.csv -------------------
            dup_output_file = os.path.join(self.output_dir, 'PRESCRIPCION_ATC_DUPLICIDADES.csv')
            with open(dup_output_file, mode='w', newline='', encoding='utf-8') as f_dup:
                dup_writer = csv.writer(f_dup)
                dup_writer.writerow([
                    'nro_definitivo', 'cod_atc', 'atc_duplicidad', 'descripcion', 'efecto', 'recomendacion'
                ])

                for pres in root.findall('ns:prescription', ns):
                    nro_def = pres.findtext('ns:nro_definitivo', '', ns)
                    atc = pres.find('ns:atc', ns)
                    cod_atc = atc.findtext('ns:cod_atc', '', ns) if atc is not None else ''
                    if atc is not None:
                        for dup in atc.findall('ns:duplicidades', ns):
                            dup_writer.writerow([
                                nro_def,
                                cod_atc,
                                dup.findtext('ns:atc_duplicidad', '', ns),
                                dup.findtext('ns:descripcion_atc_duplicidad', '', ns),
                                dup.findtext('ns:efecto_duplicidad', '', ns),
                                dup.findtext('ns:recomendacion_duplicidad', '', ns),
                            ])

            results['PRESCRIPCION_ATC_DUPLICIDADES'] = f"CSV file created successfully: {dup_output_file}"
            print(results['PRESCRIPCION_ATC_DUPLICIDADES'])

            return results

        except Exception as e:
            error_msg = f"Error processing Prescripcion XML: {str(e)}"
            print(error_msg, file=sys.stderr)
            return {'PRESCRIPCION': error_msg}

    def convert_all(self):
        """Convert all XML files to CSV format"""
        results = {}

        # Process all XML files
        processors = {
            'ATC': self.process_atc,
            'DCP': self.process_dcp,
            'DCPF': self.process_dcpf,
            'DCSA': self.process_dcsa,
            'ENVASES': self.process_envases,
            'EXCIPIENTES': self.process_excipientes,
            'FORMA_FARMACEUTICA_SIMPLIFICADAS': self.process_forma_farmaceutica_simplificadas,
            'FORMA_FARMACEUTICA': self.process_forma_farmaceutica,
            'LABORATORIOS': self.process_laboratorios,
            'UNIDAD_CONTENIDO': self.process_unidad_contenido,
            'VIAS_ADMINISTRACION': self.process_vias_administracion,
            'PRINCIPIOS_ACTIVOS': self.process_principios_activos,
            'SITUACION_REGISTRO': self.process_situacion_registro,
            'PRESCRIPCION': self.process_prescripcion
        }

        for name, processor in processors.items():
            try:
                output_file = processor()
                results[name] = f"CSV file created successfully: {output_file}"
                print(results[name])
            except Exception as e:
                results[name] = f"Error processing {name}: {str(e)}"
                print(results[name], file=sys.stderr)

        return results


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Convert XML files to CSV format')
    parser.add_argument('--input-dir', '-i', default='data', help='Input directory containing XML files')
    parser.add_argument('--output-dir', '-o', default='data/csv', help='Output directory for CSV files')

    args = parser.parse_args()

    # Create converter and run conversion
    converter = XMLToCSVConverter(args.input_dir, args.output_dir)
    converter.convert_all()
