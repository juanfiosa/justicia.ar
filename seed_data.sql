-- Datos iniciales para JUSTICIA.ar

-- ARTÍCULOS LEGALES DEL CÓDIGO CIVIL Y COMERCIAL

INSERT INTO articulos_legales (codigo, numero_articulo, texto, categoria) VALUES
('CCyC', '1716', 'Deber de reparar. La violación del deber de no dañar a otro, o el incumplimiento de una obligación, da lugar a la reparación del daño causado, conforme con las disposiciones de este Código.', 'responsabilidad_civil'),
('CCyC', '1737', 'Concepto de daño. Hay daño cuando se lesiona un derecho o un interés no reprobado por el ordenamiento jurídico, que tenga por objeto la persona, el patrimonio, o un derecho de incidencia colectiva.', 'responsabilidad_civil'),
('CCyC', '1740', 'Reparación plena. La reparación del daño debe ser plena. Consiste en la restitución de la situación del damnificado al estado anterior al hecho dañoso, sea por el pago en dinero o en especie. La víctima puede optar por el reintegro específico, excepto que sea parcial o totalmente imposible, excesivamente oneroso o abusivo, en cuyo caso se debe fijar en dinero.', 'responsabilidad_civil'),
('CCyC', '1757', 'Hecho de las cosas y actividades riesgosas. Toda persona responde por el daño causado por el riesgo o vicio de las cosas, o de las actividades que sean riesgosas o peligrosas por su naturaleza, por los medios empleados o por las circunstancias de su realización.', 'responsabilidad_civil'),
('CCyC', '1768', 'Daño moral. El daño moral es la lesión en los sentimientos que determina dolor o sufrimientos físicos, inquietud espiritual, o agravio a las afecciones legítimas y, en general, toda clase de padecimientos insusceptibles de apreciación pecuniaria.', 'responsabilidad_civil'),
('CCyC', '730', 'Efectos con relación al acreedor. El incumplimiento de una obligación, cualquiera sea su fuente, da lugar a: a) la ejecución forzada; b) el cobro de indemnización por daños; c) hacer cesar los efectos de la violación.', 'obligaciones'),
('CCyC', '1083', 'Presupuestos de la resolución por incumplimiento. Un contratante puede resolver total o parcialmente el contrato si: a) el incumplimiento es esencial; b) el incumplimiento es persistente; c) el incumplimiento no es subsanable o no fue subsanado.', 'contratos'),
('CCyC', '1031', 'Suspensión del cumplimiento. Una parte puede suspender el cumplimiento a su cargo hasta que la otra cumpla u ofrezca cumplir.', 'contratos'),
('CCyC', '729', 'Concepto de obligación. La obligación es una relación jurídica en virtud de la cual el acreedor tiene el derecho a exigir del deudor una prestación destinada a satisfacer un interés lícito.', 'obligaciones');

-- CASOS PRECEDENTES (Jurisprudencia simulada pero realista)

INSERT INTO casos_precedentes (titulo, tribunal, fecha_sentencia, hechos_resumidos, decision, monto_aproximado, tipo_caso, principios_aplicados) VALUES
('García c/ Fernández s/ Daños y Perjuicios', 'Cámara Civil y Comercial Córdoba - 8ª Nominación', '2023-05-15', 'Accidente de tránsito en intersección sin semáforo. El demandado no respetó la prioridad de paso causando daños materiales al vehículo del actor valorados en $450.000. Ambos conductores circulaban a velocidad prudencial. Hay testigos que corroboran la versión del actor.', 'Se acoge la demanda. El demandado debe indemnizar el daño material más intereses. Responsabilidad del 100% del demandado por no respetar prioridad de paso.', 450000, 'daños_perjuicios', 'Art. 1757 CCyC (responsabilidad objetiva por el riesgo de la cosa). Prioridad de paso. Nexo causal directo.'),

('Martínez c/ López s/ Incumplimiento Contractual', 'Juzgado Civil y Comercial de 1ª Instancia - 43ª Nominación', '2023-08-22', 'Contrato de compraventa de motocicleta por $380.000. El vendedor recibió el pago completo pero nunca entregó la motocicleta ni transfirió la documentación. Después de 6 meses, el comprador demanda la resolución del contrato y devolución del dinero más daños.', 'Se acoge la demanda. Resolución del contrato por incumplimiento esencial (Art. 1083 CCyC). Restitución del precio pagado más intereses moratorios más daño moral de $100.000 por la angustia y frustración causada.', 480000, 'incumplimiento_contractual', 'Art. 1083 CCyC (incumplimiento esencial). Art. 1768 (daño moral). Buena fe contractual.'),

('Rodríguez c/ Constructora del Sur SRL s/ Daños', 'Cámara Civil y Comercial Córdoba - 2ª Nominación', '2023-03-10', 'Obra en el departamento vecino causó filtraciones en el departamento del actor. Daños en pintura, revestimientos y mobiliario por valor de $280.000. La constructora reconoce los hechos pero alega caso fortuito.', 'Se acoge parcialmente. Responsabilidad objetiva de la constructora por daño causado en ejercicio de actividad riesgosa. Rechazo de la defensa de caso fortuito por falta de prueba. Se reduce el monto por tasación pericial a $250.000.', 250000, 'daños_perjuicios', 'Art. 1757 CCyC (actividad riesgosa). Carga de la prueba. Reparación plena.'),

('Pérez c/ Sánchez s/ Cobro de Pesos', 'Juzgado Civil y Comercial de 1ª Instancia - 27ª Nominación', '2023-11-05', 'Préstamo de $200.000 documentado en pagaré. Vencimiento hace 8 meses. El demandado reconoce la deuda pero alega dificultades económicas. No hay defensa sustancial.', 'Se acoge la demanda. Condena al pago del capital de $200.000 más intereses desde la mora hasta el efectivo pago, más costas del juicio.', 200000, 'cobro_suma_dinero', 'Título ejecutivo (pagaré). Mora automática. Art. 730 CCyC.'),

('Torres c/ Empresa de Mudanzas Express s/ Daños', 'Cámara Civil y Comercial Córdoba - 5ª Nominación', '2023-09-18', 'Contrato de mudanza. Durante el traslado se rompieron muebles y electrodomésticos por negligencia en el embalaje y traslado. Daño material valuado en $320.000. La empresa alega que el actor no contrató seguro adicional.', 'Se acoge parcialmente. Responsabilidad contractual de la empresa por incumplimiento de obligaciones de cuidado. La falta de seguro adicional no exime de responsabilidad básica. Condena por $280.000 considerando depreciación de bienes usados.', 280000, 'incumplimiento_contractual', 'Art. 730 y 1716 CCyC. Responsabilidad profesional. Culpa en el incumplimiento.');

-- CRITERIOS DE CLASIFICACIÓN

INSERT INTO criterios_clasificacion (factor, descripcion, peso, nivel_minimo) VALUES
('prueba_clara', 'Existencia de prueba documental clara e indiscutible (pagaré, contrato firmado, sentencia firme)', 3, 1),
('admision_hechos', 'El demandado admite los hechos o no contesta demanda', 3, 1),
('monto_bajo', 'Monto menor a $300.000', 2, 1),
('jurisprudencia_uniforme', 'Existe jurisprudencia pacífica y uniforme sobre el tipo de caso', 2, 1),
('cuestion_compleja_hecho', 'Los hechos son controvertidos o requieren prueba compleja', -2, 2),
('cuestion_compleja_derecho', 'Existe discusión doctrinaria o jurisprudencial sobre el punto de derecho', -3, 3),
('cuestion_constitucional', 'Se plantea una cuestión constitucional o de derechos fundamentales', -4, 4),
('precedente_contradictorio', 'Existen precedentes contradictorios', -2, 2),
('necesidad_pericial', 'Se requiere prueba pericial compleja', -2, 2);

-- USUARIOS DE EJEMPLO

INSERT INTO usuarios (email, nombre, rol) VALUES
('admin@justicia.gob.ar', 'Administrador Sistema', 'administrador'),
('juez.martinez@justicia.gob.ar', 'Dr. Carlos Martínez', 'funcionario'),
('juez.rodriguez@justicia.gob.ar', 'Dra. María Rodríguez', 'funcionario'),
('ciudadano1@email.com', 'Juan Pérez', 'ciudadano'),
('ciudadano2@email.com', 'Ana García', 'ciudadano');
