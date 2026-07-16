{
  "resourceType": "StructureDefinition",
  "id": "{{ profile_id }}",
  "url": "https://fhir.gulaplatform.com/StructureDefinition/{{ profile_id }}",
  "version": "1.0.0",
  "name": "{{ class_name }}",
  "title": "{{ title }}",
  "status": "draft",
  "description": "{{ description }}",
  "fhirVersion": "4.0.1",
  "kind": "resource",
  "abstract": false,
  "type": "{{ base_type }}",
  "baseDefinition": "{{ base_definition }}",
  "derivation": "constraint",
  "differential": {
    "element": [
      {
        "id": "{{ base_type }}.extension:gulaExtension",
        "path": "{{ base_type }}.extension",
        "sliceName": "gulaExtension",
        "min": 0,
        "max": "*",
        "type": [
          {
            "code": "Extension",
            "profile": [
              "https://fhir.gulaplatform.com/StructureDefinition/gula-extension"
            ]
          }
        ]
      }
    ]
  }
}
