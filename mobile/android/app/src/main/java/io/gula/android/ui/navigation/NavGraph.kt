package io.gula.android.ui.navigation

import androidx.compose.runtime.*
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import io.gula.android.ui.features.admin.AdminPanelScreen
import io.gula.android.ui.features.auth.LoginScreen
import io.gula.android.ui.features.auth.MfaScreen
import io.gula.android.ui.features.auth.RegisterScreen
import io.gula.android.ui.features.dashboard.DashboardScreen
import io.gula.android.ui.features.inventory.InventoryScreen
import io.gula.android.ui.features.notifications.NotificationListScreen
import io.gula.android.ui.features.orders.OrderCreateScreen
import io.gula.android.ui.features.orders.OrderDetailScreen
import io.gula.android.ui.features.orders.OrderListScreen
import io.gula.android.ui.features.patients.PatientDetailScreen
import io.gula.android.ui.features.patients.PatientFormScreen
import io.gula.android.ui.features.patients.PatientListScreen
import io.gula.android.ui.features.profile.ProfileScreen
import io.gula.android.ui.features.reports.ReportListScreen
import io.gula.android.ui.features.reports.ReportViewerScreen
import io.gula.android.ui.features.results.ResultDetailScreen
import io.gula.android.ui.features.results.ResultEntryScreen
import io.gula.android.ui.features.results.ResultListScreen
import io.gula.android.ui.features.results.ResultValidationScreen
import io.gula.android.ui.features.samples.SampleCollectionScreen
import io.gula.android.ui.features.samples.SampleDetailScreen
import io.gula.android.ui.features.samples.SampleListScreen
import io.gula.android.ui.features.search.GlobalSearchScreen
import io.gula.android.ui.features.settings.SettingsScreen

@Composable
fun NavGraph(
    navController: NavHostController,
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Login.route,
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onMfaRequired = { sessionId ->
                    navController.navigate(Screen.Mfa.createRoute(sessionId))
                },
                onRegister = { navController.navigate(Screen.Register.route) },
            )
        }

        composable(
            route = Screen.Mfa.route,
            arguments = listOf(navArgument("sessionId") { type = NavType.StringType }),
        ) { backStackEntry ->
            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: ""
            MfaScreen(
                sessionId = sessionId,
                onVerified = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Register.route) {
            RegisterScreen(
                onRegisterSuccess = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Register.route) { inclusive = true }
                    }
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToPatients = { navController.navigate(Screen.PatientList.route) },
                onNavigateToOrders = { navController.navigate(Screen.OrderList.route) },
                onNavigateToResults = { navController.navigate(Screen.ResultList.route) },
                onNavigateToSamples = { navController.navigate(Screen.SampleList.route) },
                onNavigateToNotifications = { navController.navigate(Screen.NotificationList.route) },
            )
        }

        composable(Screen.PatientList.route) {
            PatientListScreen(
                onPatientClick = { id -> navController.navigate(Screen.PatientDetail.createRoute(id)) },
                onAddPatient = { navController.navigate(Screen.PatientForm.createRoute()) },
                onSearch = { navController.navigate(Screen.GlobalSearch.route) },
            )
        }

        composable(
            route = Screen.PatientDetail.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            PatientDetailScreen(
                patientId = id,
                onBack = { navController.popBackStack() },
                onEdit = { navController.navigate(Screen.PatientForm.createRoute(id)) },
                onCreateOrder = { navController.navigate(Screen.OrderCreate.createRoute(id)) },
            )
        }

        composable(
            route = Screen.PatientForm.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType; defaultValue = -1 }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: -1
            PatientFormScreen(
                patientId = if (id > 0) id else null,
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() },
            )
        }

        composable(Screen.OrderList.route) {
            OrderListScreen(
                onOrderClick = { id -> navController.navigate(Screen.OrderDetail.createRoute(id)) },
                onCreateOrder = { navController.navigate(Screen.OrderCreate.createRoute()) },
            )
        }

        composable(
            route = Screen.OrderDetail.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            OrderDetailScreen(
                orderId = id,
                onBack = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.OrderCreate.route,
            arguments = listOf(navArgument("patientId") { type = NavType.IntType; defaultValue = -1 }),
        ) { backStackEntry ->
            val patientId = backStackEntry.arguments?.getInt("patientId") ?: -1
            OrderCreateScreen(
                preselectedPatientId = if (patientId > 0) patientId else null,
                onBack = { navController.popBackStack() },
                onOrderCreated = { navController.popBackStack() },
            )
        }

        composable(Screen.SampleList.route) {
            SampleListScreen(
                onSampleClick = { barcode -> navController.navigate(Screen.SampleDetail.createRoute(barcode)) },
                onCollect = { navController.navigate(Screen.SampleCollection.route) },
            )
        }

        composable(
            route = Screen.SampleDetail.route,
            arguments = listOf(navArgument("barcode") { type = NavType.StringType }),
        ) { backStackEntry ->
            val barcode = backStackEntry.arguments?.getString("barcode") ?: return@composable
            SampleDetailScreen(barcode = barcode, onBack = { navController.popBackStack() })
        }

        composable(Screen.SampleCollection.route) {
            SampleCollectionScreen(
                onBack = { navController.popBackStack() },
                onSampleCollected = { navController.popBackStack() },
            )
        }

        composable(Screen.ResultList.route) {
            ResultListScreen(
                onResultClick = { id -> navController.navigate(Screen.ResultDetail.createRoute(id)) },
                onEntry = { navController.navigate(Screen.ResultEntry.createRoute()) },
            )
        }

        composable(
            route = Screen.ResultDetail.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            ResultDetailScreen(resultId = id, onBack = { navController.popBackStack() })
        }

        composable(
            route = Screen.ResultEntry.route,
            arguments = listOf(navArgument("orderId") { type = NavType.IntType; defaultValue = -1 }),
        ) { backStackEntry ->
            val orderId = backStackEntry.arguments?.getInt("orderId") ?: -1
            ResultEntryScreen(
                orderId = if (orderId > 0) orderId else null,
                onBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.ResultValidation.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            ResultValidationScreen(resultId = id, onBack = { navController.popBackStack() }, onValidated = { navController.popBackStack() })
        }

        composable(Screen.NotificationList.route) {
            NotificationListScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.ReportList.route) {
            ReportListScreen(
                onReportClick = { id -> navController.navigate(Screen.ReportViewer.createRoute(id)) },
                onBack = { navController.popBackStack() },
            )
        }

        composable(
            route = Screen.ReportViewer.route,
            arguments = listOf(navArgument("id") { type = NavType.IntType }),
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getInt("id") ?: return@composable
            ReportViewerScreen(reportId = id, onBack = { navController.popBackStack() })
        }

        composable(Screen.Inventory.route) {
            InventoryScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onBack = { navController.popBackStack() },
                onNavigateToProfile = { navController.navigate(Screen.Profile.route) },
            )
        }

        composable(Screen.Profile.route) {
            ProfileScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.GlobalSearch.route) {
            GlobalSearchScreen(
                onBack = { navController.popBackStack() },
                onPatientClick = { id -> navController.navigate(Screen.PatientDetail.createRoute(id)) },
                onOrderClick = { id -> navController.navigate(Screen.OrderDetail.createRoute(id)) },
            )
        }

        composable(Screen.AdminPanel.route) {
            AdminPanelScreen(onBack = { navController.popBackStack() })
        }
    }
}
