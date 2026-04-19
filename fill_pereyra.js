// CASO PEREYRA — pegar en la consola del navegador (F12 → Console)
// Llena todos los campos del formulario automáticamente

(function() {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return console.warn('No encontré:', id);
    el.value = val;
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('input',  { bubbles: true }));
  };

  // I. Identificación
  set('caratula',    'Pereyra, Luciana Beatriz p.s.a. Homicidio culposo agravado (art. 84 bis CP)');
  set('expediente',  '8814/2025');
  set('rama',        'penal');
  set('tipo_proceso','juicio oral');
  set('tribunal',    'Tribunal Oral en lo Criminal Nro. 3 de Mendoza');
  set('jurisdiccion','Mendoza');
  set('instancia',   'primera');

  // Disparar el cambio de instancia para que aparezcan los paneles
  document.getElementById('instancia')?.dispatchEvent(new Event('change', { bubbles: true }));

  // II. Hechos probados
  set('hechos_probados',
    'El 22 de febrero de 2025, a las 08:10 hs, la imputada Luciana Beatriz Pereyra ' +
    'conducía su automóvil Toyota Corolla por Av. San Martín al 4500 de Mendoza capital ' +
    'cuando atropelló al peatón Gustavo Marcelo Ibáñez, de 72 años, quien cruzaba por la ' +
    'senda peatonal con el semáforo a su favor. Ibáñez falleció en el Hospital Central cuatro ' +
    'horas después a causa de un traumatismo encéfalo-craneano grave. Pereyra no estaba ' +
    'alcoholizada (0,0 g/l) pero en el momento del impacto estaba mirando el celular según ' +
    'surge de las pericias.'
  );

  // III. Partes — Fiscalía (actor)
  set('actor_nombre',     'Ministerio Público Fiscal de Mendoza');
  set('actor_letrado',    'Dr. Rodrigo Castellanos (Fiscal de Juicio)');
  set('actor_pretension', '3 años de prisión en suspenso, inhabilitación especial para conducir por 5 años, art. 84 bis segundo párrafo CP.');
  set('actor_fundamentos',
    'La pericia informática sobre el celular de Pereyra registra actividad de WhatsApp ' +
    '4 minutos antes del impacto y la pantalla encendida según el sensor de proximidad. ' +
    'El testigo Fagúndez vio a Pereyra con el celular en la mano inmediatamente antes del impacto. ' +
    'Las cámaras de tránsito muestran que Ibáñez cruzaba por la senda peatonal. ' +
    'El camión en doble fila era visible a 30 metros. ' +
    'Conducir con celular configura la agravante del art. 84 bis segundo párrafo CP.'
  );

  // III. Partes — Defensa (demandado)
  set('demandado_nombre',     'Luciana Beatriz Pereyra, DNI 29.114.302, 38 años');
  set('demandado_letrado',    'Dra. Mariana Solís (defensa particular)');
  set('demandado_pretension', 'Absolución. Subsidiariamente, atenuantes por falta de antecedentes y conducta posterior (llamó al SAME).');
  set('demandado_fundamentos',
    'La defensa niega que Pereyra estuviera usando el celular al momento del impacto. ' +
    'La pericia solo determina la última actividad registrada 4 minutos antes del accidente, ' +
    'no durante el mismo. El perito de parte sostiene que el impacto se produjo porque Ibáñez ' +
    'cruzó en zona de visibilidad reducida por un camión estacionado en doble fila. ' +
    'Art. 84 bis CP. Art. 1729 CCyC (culpa de la víctima). ' +
    'TSJ Mendoza "Díaz, Roberto" (2023) sobre estándar probatorio en siniestros viales con celular.'
  );

  // IV. Valoración de la prueba
  set('valoracion_prueba',
    'La pericia informática no acredita fehacientemente el uso del celular durante el impacto: ' +
    'solo registra actividad previa y pantalla encendida, lo que es insuficiente para establecer ' +
    'distracción al momento exacto del accidente. Sin embargo, el testimonio de Fagúndez —quien vio ' +
    'a Pereyra con el celular en la mano segundos antes del impacto— es claro, desinteresado y no ' +
    'fue eficazmente contradicho por la defensa. Las cámaras confirman que Ibáñez cruzaba por la ' +
    'senda habilitada con semáforo a su favor. El camión en doble fila no obstruía la visibilidad ' +
    'desde la distancia a la que Pereyra debía haber percibido al peatón si prestaba atención. ' +
    'Tengo por acreditado que Pereyra conducía con el celular en la mano al momento del impacto, ' +
    'configurándose la agravante del art. 84 bis segundo párrafo CP. No acredito culpa concurrente de la víctima.'
  );

  // Nivel de complejidad
  const radio2 = document.querySelector('input[name="nivel_complejidad"][value="2"]');
  if (radio2) { radio2.checked = true; radio2.dispatchEvent(new Event('change', { bubbles: true })); }

  console.log('✅ Formulario completado. Hacé clic en CLASIFICAR CASO y luego GENERAR.');
})();
