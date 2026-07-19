package io.gula.android.ui

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.navigation.testing.TestNavHostController
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NavigationTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private lateinit var navController: TestNavHostController

    @Before
    fun setup() {
        composeTestRule.setContent {
            navController = TestNavHostController(
                ApplicationProvider.getApplicationContext()
            )
        }
    }

    @Test
    fun appLaunchesToLoginScreen() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        composeTestRule.onNodeWithText("Sign In").assertIsDisplayed()
    }

    @Test
    fun navigateFromLoginToRegister() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("register")
        composeTestRule.onNodeWithText("Create Account").assertIsDisplayed()
    }

    @Test
    fun navigateFromLoginToMfa() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("mfa")
        composeTestRule.onNodeWithText("Two-Factor Authentication").assertIsDisplayed()
    }

    @Test
    fun navigateToDashboard() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("main/dashboard")
        composeTestRule.onNodeWithText("Dashboard").assertIsDisplayed()
    }

    @Test
    fun navigateToPatients() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("main/patients")
        composeTestRule.onNodeWithText("Patients").assertIsDisplayed()
    }

    @Test
    fun navigateToOrders() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("main/orders")
        composeTestRule.onNodeWithText("Orders").assertIsDisplayed()
    }

    @Test
    fun navigateToResults() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("main/results")
        composeTestRule.onNodeWithText("Results").assertIsDisplayed()
    }

    @Test
    fun navigateToNotifications() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("notifications")
        composeTestRule.onNodeWithText("Notifications").assertIsDisplayed()
    }

    @Test
    fun navigateToSettings() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("main/settings")
        composeTestRule.onNodeWithText("Settings").assertIsDisplayed()
    }

    @Test
    fun navigateToPatientDetail() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("patient/test-id")
        composeTestRule.onNodeWithText("Patient Details").assertIsDisplayed()
    }

    @Test
    fun navigateToOrderDetail() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("order/test-order-id")
        composeTestRule.onNodeWithText("Order Details").assertIsDisplayed()
    }

    @Test
    fun navigateToResultDetail() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("result/test-result-id")
        composeTestRule.onNodeWithText("Result Details").assertIsDisplayed()
    }

    @Test
    fun navigateToSampleDetail() {
        composeTestRule.setContent {
            NavGraph(navController = navController)
        }

        navController.navigate("samples")
        composeTestRule.onNodeWithText("Samples").assertIsDisplayed()
    }
}
