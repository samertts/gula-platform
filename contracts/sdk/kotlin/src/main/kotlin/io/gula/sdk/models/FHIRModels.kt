package io.gula.sdk.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class FHIRPatient(
    val id: String? = null,
    @SerialName("resourceType") val resourceType: String = "Patient",
    val identifier: List<FHIRIdentifier>? = null,
    val name: List<FHIRHumanName>? = null,
    val telecom: List<FHIRContactPoint>? = null,
    val gender: String? = null,
    @SerialName("birthDate") val birthDate: String? = null,
    val address: List<FHIRAddress>? = null,
    @SerialName("managingOrganization") val managingOrganization: FHIRReference? = null,
    @SerialName("generalPractitioner") val generalPractitioner: List<FHIRReference>? = null,
)

@Serializable
data class FHIRIdentifier(
    val use: String? = null,
    val type: FHIRCodeableConcept? = null,
    val system: String? = null,
    val value: String? = null,
    val period: FHIRPeriod? = null,
)

@Serializable
data class FHIRHumanName(
    val use: String? = null,
    val text: String? = null,
    val family: String? = null,
    val given: List<String>? = null,
    val prefix: List<String>? = null,
    val suffix: List<String>? = null,
)

@Serializable
data class FHIRContactPoint(
    val system: String? = null,
    val value: String? = null,
    val use: String? = null,
)

@Serializable
data class FHIRAddress(
    val use: String? = null,
    val type: String? = null,
    val text: String? = null,
    val line: List<String>? = null,
    val city: String? = null,
    val district: String? = null,
    val state: String? = null,
    @SerialName("postalCode") val postalCode: String? = null,
    val country: String? = null,
)

@Serializable
data class FHIRReference(
    val reference: String? = null,
    val type: String? = null,
    val identifier: FHIRIdentifier? = null,
    val display: String? = null,
)

@Serializable
data class FHIRCodeableConcept(
    val coding: List<FHIRCoding>? = null,
    val text: String? = null,
)

@Serializable
data class FHIRCoding(
    val system: String? = null,
    val code: String? = null,
    val display: String? = null,
)

@Serializable
data class FHIRPeriod(
    val start: String? = null,
    val end: String? = null,
)

@Serializable
data class FHIRObservation(
    val id: String? = null,
    @SerialName("resourceType") val resourceType: String = "Observation",
    val status: String = "final",
    val category: List<FHIRCodeableConcept>? = null,
    val code: FHIRCodeableConcept,
    val subject: FHIRReference? = null,
    val encounter: FHIRReference? = null,
    @SerialName("effectiveDateTime") val effectiveDateTime: String? = null,
    @SerialName("issued") val issued: String? = null,
    val performer: List<FHIRReference>? = null,
    @SerialName("valueQuantity") val valueQuantity: FHIRQuantity? = null,
    @SerialName("valueCodeableConcept") val valueCodeableConcept: FHIRCodeableConcept? = null,
    @SerialName("valueString") val valueString: String? = null,
    val interpretation: List<FHIRCodeableConcept>? = null,
    @SerialName("referenceRange") val referenceRange: List<FHIRReferenceRange>? = null,
)

@Serializable
data class FHIRQuantity(
    val value: Double? = null,
    val comparator: String? = null,
    val unit: String? = null,
    val system: String? = null,
    val code: String? = null,
)

@Serializable
data class FHIRReferenceRange(
    val low: FHIRSimpleQuantity? = null,
    val high: FHIRSimpleQuantity? = null,
    val type: FHIRCodeableConcept? = null,
    val text: String? = null,
)

@Serializable
data class FHIRSimpleQuantity(
    val value: Double? = null,
    val unit: String? = null,
    val system: String? = null,
    val code: String? = null,
)

@Serializable
data class FHIRServiceRequest(
    val id: String? = null,
    @SerialName("resourceType") val resourceType: String = "ServiceRequest",
    val status: String = "active",
    val intent: String = "order",
    val code: FHIRCodeableConcept,
    val subject: FHIRReference? = null,
    @SerialName("requester") val requester: FHIRReference? = null,
    @SerialName("performer") val performer: List<FHIRReference>? = null,
    @SerialName("occurrenceDateTime") val occurrenceDateTime: String? = null,
    val note: List<FHIRAnnotation>? = null,
)

@Serializable
data class FHIRAnnotation(
    val authorReference: FHIRReference? = null,
    val authorString: String? = null,
    val time: String? = null,
    val text: String? = null,
)

@Serializable
data class FHIRBundle(
    val id: String? = null,
    @SerialName("resourceType") val resourceType: String = "Bundle",
    val type: String = "collection",
    val timestamp: String? = null,
    val total: Int? = null,
    val entry: List<FHIRBundleEntry>? = null,
)

@Serializable
data class FHIRBundleEntry(
    val fullUrl: String? = null,
    val resource: kotlinx.serialization.json.JsonElement? = null,
    val request: FHIRBundleRequest? = null,
    val response: FHIRBundleResponse? = null,
)

@Serializable
data class FHIRBundleRequest(
    val method: String? = null,
    val url: String? = null,
)

@Serializable
data class FHIRBundleResponse(
    val status: String? = null,
    val location: String? = null,
    val etag: String? = null,
)
