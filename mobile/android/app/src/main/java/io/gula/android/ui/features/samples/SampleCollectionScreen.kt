package io.gula.android.ui.features.samples

import android.Manifest
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.google.accompanist.permissions.*
import io.gula.android.ui.components.core.GulaButton
import io.gula.android.ui.components.core.GulaTextField
import java.util.concurrent.Executors

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun SampleCollectionScreen(
    onBack: () -> Unit,
    onSampleCollected: () -> Unit,
    viewModel: SamplesViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    var orderId by remember { mutableStateOf("") }
    var sampleType by remember { mutableStateOf("") }
    var manualBarcode by remember { mutableStateOf("") }
    var useCamera by remember { mutableStateOf(true) }
    val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val cameraExecutor = remember { Executors.newSingleThreadExecutor() }

    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) onSampleCollected()
    }

    Scaffold(
        topBar = {
            androidx.compose.material3.CenterAlignedTopAppBar(
                title = { Text("Collect Sample") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
            ) {
                FilterChip(
                    selected = useCamera,
                    onClick = {
                        useCamera = true
                        if (cameraPermissionState.status.isGranted.not()) {
                            cameraPermissionState.launchPermissionRequest()
                        }
                    },
                    label = { Text("Scan Barcode") },
                    leadingIcon = { Icon(Icons.Default.QrCodeScanner, contentDescription = null, modifier = Modifier.size(16.dp)) },
                )
                Spacer(Modifier.width(8.dp))
                FilterChip(
                    selected = !useCamera,
                    onClick = { useCamera = false },
                    label = { Text("Manual Entry") },
                    leadingIcon = { Icon(Icons.Default.Keyboard, contentDescription = null, modifier = Modifier.size(16.dp)) },
                )
            }

            if (useCamera) {
                if (cameraPermissionState.status.isGranted) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(250.dp),
                    ) {
                        AndroidView(
                            factory = { ctx ->
                                val previewView = PreviewView(ctx)
                                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                                cameraProviderFuture.addListener({
                                    val cameraProvider = cameraProviderFuture.get()
                                    val preview = Preview.Builder().build().also {
                                        it.setSurfaceProvider(previewView.surfaceProvider)
                                    }
                                    val imageAnalysis = ImageAnalysis.Builder()
                                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                        .build()
                                    imageAnalysis.setAnalyzer(cameraExecutor) { imageProxy ->
                                        imageProxy.close()
                                    }
                                    val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
                                    try {
                                        cameraProvider.unbindAll()
                                        cameraProvider.bindToLifecycle(
                                            lifecycleOwner, cameraSelector, preview, imageAnalysis
                                        )
                                    } catch (e: Exception) { }
                                }, ContextCompat.getMainExecutor(ctx))
                                previewView
                            },
                            modifier = Modifier.fillMaxSize(),
                        )
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center,
                        ) {
                            Surface(
                                modifier = Modifier.size(250.dp, 40.dp),
                                color = MaterialTheme.colorScheme.error.copy(alpha = 0.3f),
                            ) {}
                        }
                    }
                } else {
                    Button(onClick = { cameraPermissionState.launchPermissionRequest() }) {
                        Text("Grant Camera Permission")
                    }
                }
            } else {
                GulaTextField(
                    value = manualBarcode,
                    onValueChange = { manualBarcode = it; viewModel.setBarcode(it) },
                    label = "Barcode",
                    placeholder = "Scan or enter barcode",
                    leadingIcon = Icons.Default.Barcode,
                )
            }

            GulaTextField(
                value = orderId,
                onValueChange = { orderId = it },
                label = "Order ID",
                placeholder = "Enter order ID",
                leadingIcon = Icons.Default.Assignment,
                keyboardType = KeyboardType.Number,
            )

            GulaTextField(
                value = sampleType,
                onValueChange = { sampleType = it },
                label = "Sample Type",
                placeholder = "e.g., Blood, Urine",
                leadingIcon = Icons.Default.Biotech,
            )

            if (uiState.error != null) {
                Text(uiState.error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }

            Spacer(Modifier.weight(1f))

            GulaButton(
                onClick = {
                    val barcode = if (useCamera) uiState.scannedBarcode else manualBarcode
                    if (orderId.isNotBlank() && sampleType.isNotBlank()) {
                        viewModel.createSample(orderId.toInt(), sampleType)
                    }
                },
                text = "Collect Sample",
                loading = uiState.isSaving,
                modifier = Modifier.fillMaxWidth(),
                icon = Icons.Default.CheckCircle,
                enabled = orderId.isNotBlank() && sampleType.isNotBlank(),
            )
        }
    }
}
