package io.gula.android

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.rememberNavController
import dagger.hilt.android.AndroidEntryPoint
import io.gula.android.data.remote.api.GulaApi
import io.gula.android.data.remote.api.UpdatePolicyDto
import io.gula.android.ui.navigation.NavGraph
import io.gula.android.ui.theme.GulaTheme
import javax.inject.Inject
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var gulaApi: GulaApi

    private var updatePolicy by mutableStateOf<UpdatePolicyDto?>(null)
    private var updateCheckCompleted by mutableStateOf(false)
    private var optionalDialogDismissed by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        checkForUpdates()
        setContent {
            GulaTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val policy = updatePolicy
                    when {
                        !updateCheckCompleted -> {
                            Column(
                                modifier = Modifier.fillMaxSize(),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center,
                            ) {
                                CircularProgressIndicator()
                            }
                        }
                        policy?.forceUpdate == true -> {
                            UpdateRequiredScreen(
                                policy = policy,
                                onUpdate = ::openUpdateLink,
                            )
                        }
                        else -> {
                            val navController = rememberNavController()
                            NavGraph(navController = navController)
                            if (policy?.updateAvailable == true && !optionalDialogDismissed) {
                                AlertDialog(
                                    onDismissRequest = { optionalDialogDismissed = true },
                                    title = { Text("يتوفر تحديث جديد") },
                                    text = {
                                        Text(
                                            policy.messageAr.ifBlank {
                                                "يتوفر إصدار أحدث من منصة GULA."
                                            },
                                        )
                                    },
                                    confirmButton = {
                                        Button(onClick = ::openUpdateLink) {
                                            Text("تحديث الآن")
                                        }
                                    },
                                    dismissButton = {
                                        Button(onClick = { optionalDialogDismissed = true }) {
                                            Text("لاحقًا")
                                        }
                                    },
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    private fun checkForUpdates() {
        lifecycleScope.launch {
            updatePolicy = runCatching {
                gulaApi.getUpdateManifest(version = BuildConfig.VERSION_NAME)
                    .body()
                    ?.policies
                    ?.get("android")
            }.getOrNull()
            // A temporary manifest outage must not block clinical access.
            updateCheckCompleted = true
        }
    }

    private fun openUpdateLink() {
        val url = updatePolicy?.storeUrl ?: "https://play.google.com/store/apps/details?id=io.gula.android"
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }
}

@androidx.compose.runtime.Composable
private fun UpdateRequiredScreen(
    policy: UpdatePolicyDto,
    onUpdate: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = "يلزم تحديث التطبيق للمتابعة",
            style = MaterialTheme.typography.headlineSmall,
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = policy.messageAr.ifBlank { "يرجى تثبيت أحدث إصدار من GULA." },
            style = MaterialTheme.typography.bodyLarge,
        )
        Spacer(modifier = Modifier.height(24.dp))
        Button(onClick = onUpdate) {
            Text("تحديث الآن")
        }
    }
}
