package io.gula.android.ui.navigation

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Mfa : Screen("mfa/{sessionId}") {
        fun createRoute(sessionId: String) = "mfa/$sessionId"
    }
    data object Register : Screen("register")
    data object ForgotPassword : Screen("forgot_password")
    data object Dashboard : Screen("dashboard")
    data object PatientList : Screen("patients")
    data object PatientDetail : Screen("patients/{id}") {
        fun createRoute(id: Int) = "patients/$id"
    }
    data object PatientForm : Screen("patients/form?id={id}") {
        fun createRoute(id: Int? = null) = if (id != null) "patients/form?id=$id" else "patients/form"
    }
    data object OrderList : Screen("orders")
    data object OrderDetail : Screen("orders/{id}") {
        fun createRoute(id: Int) = "orders/$id"
    }
    data object OrderCreate : Screen("orders/create?patientId={patientId}") {
        fun createRoute(patientId: Int? = null) = if (patientId != null) "orders/create?patientId=$patientId" else "orders/create"
    }
    data object SampleList : Screen("samples")
    data object SampleDetail : Screen("samples/{barcode}") {
        fun createRoute(barcode: String) = "samples/$barcode"
    }
    data object SampleCollection : Screen("samples/collection")
    data object ResultList : Screen("results")
    data object ResultDetail : Screen("results/{id}") {
        fun createRoute(id: Int) = "results/$id"
    }
    data object ResultEntry : Screen("results/entry?orderId={orderId}") {
        fun createRoute(orderId: Int? = null) = if (orderId != null) "results/entry?orderId=$orderId" else "results/entry"
    }
    data object ResultValidation : Screen("results/validation/{id}") {
        fun createRoute(id: Int) = "results/validation/$id"
    }
    data object NotificationList : Screen("notifications")
    data object ReportList : Screen("reports")
    data object ReportViewer : Screen("reports/{id}") {
        fun createRoute(id: Int) = "reports/$id"
    }
    data object Inventory : Screen("inventory")
    data object Settings : Screen("settings")
    data object Profile : Screen("profile")
    data object GlobalSearch : Screen("search")
    data object AdminPanel : Screen("admin")
}
