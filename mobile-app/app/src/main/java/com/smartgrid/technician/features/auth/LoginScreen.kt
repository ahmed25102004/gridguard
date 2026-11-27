package com.smartgrid.technician.features.auth

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.smartgrid.technician.core.network.ApiConfig
import com.smartgrid.technician.ui.theme.AppOutline
import com.smartgrid.technician.ui.theme.AppTextPrimary
import com.smartgrid.technician.ui.theme.ElectricBlue
import com.smartgrid.technician.ui.theme.ElectricBlueDark
import com.smartgrid.technician.ui.theme.ElectricBlueDeep
import com.smartgrid.technician.ui.theme.ElectricBlueLight
import com.smartgrid.technician.ui.theme.SlateBlue

object LoginScreenTags {
    const val EMAIL_FIELD = "login_email_field"
    const val PASSWORD_FIELD = "login_password_field"
    const val LOGIN_BUTTON = "login_submit_button"
    const val PASSWORD_TOGGLE = "login_password_toggle"
    const val ERROR_BANNER = "login_error_banner"
    const val CONNECTIVITY_STATUS = "login_connectivity_status"
    const val LOADING_INDICATOR = "login_loading_indicator"
}

@Composable
fun LoginScreen(
    viewModel: AuthViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val focusManager = LocalFocusManager.current
    val scrollState = rememberScrollState()

    var showServerDialog by remember { mutableStateOf(false) }
    var serverUrlInput by remember { mutableStateOf(ApiConfig.defaultBaseUrl) }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.White)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
        ) {
            // ── HERO HEADER WITH TRANSMISSION TOWER SILHOUETTES ──────────
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(290.dp)
                    .background(
                        brush = Brush.verticalGradient(
                            colors = listOf(
                                ElectricBlueDeep,
                                ElectricBlueDark,
                                ElectricBlue,
                                ElectricBlueLight.copy(alpha = 0.9f)
                            )
                        )
                    )
            ) {
                // Subtle Electricity Transmission Tower Silhouettes
                TransmissionTowerBackdrop(
                    modifier = Modifier.fillMaxSize()
                )

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .statusBarsPadding()
                        .padding(horizontal = 24.dp, vertical = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    ConnectivityStatusPill(
                        isOnline = uiState.isOnline,
                        modifier = Modifier.testTag(LoginScreenTags.CONNECTIVITY_STATUS)
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    Box(
                        modifier = Modifier
                            .size(72.dp)
                            .clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.16f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Bolt,
                            contentDescription = "Smart Grid Platform Icon",
                            tint = Color.White,
                            modifier = Modifier.size(42.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = "Smart Grid Asset Platform",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Field Technician Secure Portal",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.85f),
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(16.dp))
                }
            }

            // ── ROUNDED WHITE FORM SHEET ─────────────────────────────────
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .offset(y = (-24).dp),
                shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp),
                color = Color.White
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 24.dp, vertical = 28.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Welcome Back",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = AppTextPrimary
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Sign in to your account",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SlateBlue
                    )

                    Spacer(modifier = Modifier.height(22.dp))

                    // Error Banner
                    AnimatedVisibility(
                        visible = uiState.errorMessage != null,
                        enter = fadeIn(),
                        exit = fadeOut()
                    ) {
                        uiState.errorMessage?.let { errorText ->
                            ErrorNotificationCard(
                                message = errorText,
                                errorType = uiState.errorType,
                                onDismiss = { viewModel.dismissError() },
                                onEnterOffline = { viewModel.enterOfflineFieldMode() },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .testTag(LoginScreenTags.ERROR_BANNER)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                        }
                    }

                    // Offline Advisory
                    AnimatedVisibility(
                        visible = !uiState.isOnline,
                        enter = fadeIn(),
                        exit = fadeOut()
                    ) {
                        OfflineAdvisoryCard(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 16.dp)
                        )
                    }

                    // Email Input Field
                    OutlinedTextField(
                        value = uiState.email,
                        onValueChange = { viewModel.onEmailChange(it) },
                        label = { Text("Technician Email") },
                        placeholder = { Text("technician@smartgrid.com") },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Default.Email,
                                contentDescription = "Email Icon",
                                tint = SlateBlue
                            )
                        },
                        isError = uiState.emailError != null,
                        supportingText = {
                            uiState.emailError?.let {
                                Text(
                                    text = it,
                                    color = MaterialTheme.colorScheme.error,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        },
                        singleLine = true,
                        enabled = !uiState.isLoading,
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Email,
                            imeAction = ImeAction.Next
                        ),
                        keyboardActions = KeyboardActions(
                            onNext = { focusManager.moveFocus(FocusDirection.Down) }
                        ),
                        shape = RoundedCornerShape(14.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = ElectricBlue,
                            unfocusedBorderColor = AppOutline,
                            focusedLabelColor = ElectricBlue,
                            unfocusedLabelColor = SlateBlue,
                            cursorColor = ElectricBlue,
                            focusedContainerColor = Color(0xFFFAFBFD),
                            unfocusedContainerColor = Color(0xFFFAFBFD)
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag(LoginScreenTags.EMAIL_FIELD)
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    // Password Input Field
                    OutlinedTextField(
                        value = uiState.password,
                        onValueChange = { viewModel.onPasswordChange(it) },
                        label = { Text("Password") },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Default.Lock,
                                contentDescription = "Password Icon",
                                tint = SlateBlue
                            )
                        },
                        trailingIcon = {
                            IconButton(
                                onClick = { viewModel.togglePasswordVisibility() },
                                modifier = Modifier.testTag(LoginScreenTags.PASSWORD_TOGGLE)
                            ) {
                                Icon(
                                    imageVector = if (uiState.isPasswordVisible) {
                                        Icons.Default.VisibilityOff
                                    } else {
                                        Icons.Default.Visibility
                                    },
                                    contentDescription = if (uiState.isPasswordVisible) "Hide password" else "Show password",
                                    tint = SlateBlue
                                )
                            }
                        },
                        visualTransformation = if (uiState.isPasswordVisible) {
                            VisualTransformation.None
                        } else {
                            PasswordVisualTransformation()
                        },
                        isError = uiState.passwordError != null,
                        supportingText = {
                            uiState.passwordError?.let {
                                Text(
                                    text = it,
                                    color = MaterialTheme.colorScheme.error,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        },
                        singleLine = true,
                        enabled = !uiState.isLoading,
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Password,
                            imeAction = ImeAction.Done
                        ),
                        keyboardActions = KeyboardActions(
                            onDone = {
                                focusManager.clearFocus()
                                viewModel.login()
                            }
                        ),
                        shape = RoundedCornerShape(14.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = ElectricBlue,
                            unfocusedBorderColor = AppOutline,
                            focusedLabelColor = ElectricBlue,
                            unfocusedLabelColor = SlateBlue,
                            cursorColor = ElectricBlue,
                            focusedContainerColor = Color(0xFFFAFBFD),
                            unfocusedContainerColor = Color(0xFFFAFBFD)
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag(LoginScreenTags.PASSWORD_FIELD)
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    // Primary Blue Login Button
                    Button(
                        onClick = {
                            focusManager.clearFocus()
                            viewModel.login()
                        },
                        enabled = uiState.isLoginEnabled,
                        shape = RoundedCornerShape(14.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(54.dp)
                            .testTag(LoginScreenTags.LOGIN_BUTTON),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = ElectricBlue,
                            disabledContainerColor = ElectricBlue.copy(alpha = 0.45f)
                        ),
                        elevation = ButtonDefaults.buttonElevation(
                            defaultElevation = 3.dp,
                            pressedElevation = 1.dp
                        )
                    ) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator(
                                color = Color.White,
                                strokeWidth = 2.5.dp,
                                modifier = Modifier
                                    .size(22.dp)
                                    .testTag(LoginScreenTags.LOADING_INDICATOR)
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "Authenticating...",
                                style = MaterialTheme.typography.labelLarge,
                                color = Color.White
                            )
                        } else {
                            Text(
                                text = "Authenticate",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // OR Divider matching reference image
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        HorizontalDivider(
                            modifier = Modifier.weight(1f),
                            color = AppOutline.copy(alpha = 0.7f)
                        )
                        Text(
                            text = "OR",
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = SlateBlue,
                            modifier = Modifier.padding(horizontal = 14.dp)
                        )
                        HorizontalDivider(
                            modifier = Modifier.weight(1f),
                            color = AppOutline.copy(alpha = 0.7f)
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Offline Field Access Button (matches secondary outlined pill in reference)
                    OutlinedButton(
                        onClick = {
                            focusManager.clearFocus()
                            viewModel.enterOfflineFieldMode()
                        },
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(1.2.dp, AppOutline),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = Color.White,
                            contentColor = AppTextPrimary
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.WifiOff,
                            contentDescription = null,
                            tint = ElectricBlue,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Offline Field Access (دخول بدون اتصال)",
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.SemiBold,
                            color = AppTextPrimary
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    // Security Notice Footer
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Shield,
                            contentDescription = null,
                            tint = ElectricBlue,
                            modifier = Modifier.size(15.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Secure • Android Keystore & AES-256 SQLCipher",
                            style = MaterialTheme.typography.labelSmall,
                            color = SlateBlue,
                            textAlign = TextAlign.Center
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Server Configuration Button (for physical device LAN IP testing)
                    TextButton(
                        onClick = { showServerDialog = true }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = null,
                            modifier = Modifier.size(15.dp),
                            tint = SlateBlue
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Server Configuration (إعدادات عنوان السيرفر)",
                            style = MaterialTheme.typography.labelSmall,
                            color = SlateBlue
                        )
                    }
                }
            }
        }

        if (showServerDialog) {
            AlertDialog(
                onDismissRequest = { showServerDialog = false },
                title = { Text("Server Configuration") },
                text = {
                    Column {
                        Text(
                            text = "Enter PC IP for live testing on a physical phone over Wi-Fi (e.g. http://192.168.1.15:8000/):",
                            style = MaterialTheme.typography.bodySmall,
                            color = SlateBlue
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = serverUrlInput,
                            onValueChange = { serverUrlInput = it },
                            label = { Text("API Base URL") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            TextButton(onClick = { serverUrlInput = "http://10.0.2.2:8000/" }) {
                                Text("10.0.2.2")
                            }
                            TextButton(onClick = { serverUrlInput = "http://localhost:8000/" }) {
                                Text("localhost")
                            }
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            ApiConfig.customBaseUrl = serverUrlInput.trim()
                            showServerDialog = false
                        }
                    ) {
                        Text("Save & Apply")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showServerDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }

        // Cold-start Session Checking Overlay
        if (uiState.authState is AuthState.CheckingSession) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.White.copy(alpha = 0.90f)),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    CircularProgressIndicator(color = ElectricBlue)
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Restoring secure technician session...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = AppTextPrimary
                    )
                }
            }
        }
    }
}

/**
 * Draws subtle architectural electricity transmission tower silhouettes
 * in the hero header background to match the visual identity.
 */
@Composable
private fun TransmissionTowerBackdrop(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier) {
        val w = size.width
        val h = size.height
        val lineColor = Color.White.copy(alpha = 0.12f)
        val stroke = Stroke(width = 2.2f)

        fun drawTower(cx: Float, baseWidth: Float, topY: Float) {
            val path = Path().apply {
                // Left and right legs
                moveTo(cx - baseWidth * 0.5f, h)
                lineTo(cx - baseWidth * 0.12f, topY + 28f)
                lineTo(cx, topY)
                lineTo(cx + baseWidth * 0.12f, topY + 28f)
                lineTo(cx + baseWidth * 0.5f, h)

                // Upper cross-arm
                moveTo(cx - baseWidth * 0.45f, topY + 52f)
                lineTo(cx + baseWidth * 0.45f, topY + 52f)

                // Lower cross-arm
                moveTo(cx - baseWidth * 0.58f, topY + 100f)
                lineTo(cx + baseWidth * 0.58f, topY + 100f)

                // Diagonal lattice braces
                moveTo(cx - baseWidth * 0.28f, h * 0.68f)
                lineTo(cx + baseWidth * 0.28f, h * 0.68f)
                moveTo(cx - baseWidth * 0.36f, h * 0.84f)
                lineTo(cx + baseWidth * 0.36f, h * 0.84f)
            }
            drawPath(path, color = lineColor, style = stroke)
        }

        drawTower(cx = w * 0.16f, baseWidth = w * 0.24f, topY = h * 0.18f)
        drawTower(cx = w * 0.84f, baseWidth = w * 0.20f, topY = h * 0.26f)

        // Subtle power lines connecting towers
        drawLine(
            color = Color.White.copy(alpha = 0.08f),
            start = Offset(0f, h * 0.34f),
            end = Offset(w, h * 0.42f),
            strokeWidth = 1.5f
        )
        drawLine(
            color = Color.White.copy(alpha = 0.08f),
            start = Offset(0f, h * 0.48f),
            end = Offset(w, h * 0.55f),
            strokeWidth = 1.5f
        )
    }
}

@Composable
fun ConnectivityStatusPill(
    isOnline: Boolean,
    modifier: Modifier = Modifier
) {
    val backgroundColor = if (isOnline) {
        Color.White.copy(alpha = 0.20f)
    } else {
        Color(0xFFC62828).copy(alpha = 0.85f)
    }

    Row(
        modifier = modifier
            .clip(RoundedCornerShape(20.dp))
            .background(backgroundColor)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = if (isOnline) Icons.Default.Wifi else Icons.Default.WifiOff,
            contentDescription = if (isOnline) "Network Online" else "Network Offline",
            tint = Color.White,
            modifier = Modifier.size(15.dp)
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = if (isOnline) "Online — Network Connected" else "Offline — Cellular/Wi-Fi Disconnected",
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Medium,
            color = Color.White
        )
    }
}

@Composable
fun ErrorNotificationCard(
    message: String,
    errorType: AuthErrorType?,
    onDismiss: () -> Unit,
    onEnterOffline: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = when (errorType) {
                        AuthErrorType.NETWORK_UNAVAILABLE -> Icons.Default.WifiOff
                        AuthErrorType.INVALID_CREDENTIALS -> Icons.Default.Lock
                        else -> Icons.Default.ErrorOutline
                    },
                    contentDescription = "Error Icon",
                    tint = MaterialTheme.colorScheme.onErrorContainer,
                    modifier = Modifier.size(22.dp)
                )

                Spacer(modifier = Modifier.width(10.dp))

                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onErrorContainer,
                    modifier = Modifier.weight(1f)
                )

                IconButton(
                    onClick = onDismiss,
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Dismiss error",
                        tint = MaterialTheme.colorScheme.onErrorContainer,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            val isNetworkIssue = errorType == AuthErrorType.NETWORK_UNAVAILABLE ||
                errorType == AuthErrorType.SERVER_ERROR ||
                message.contains("reach", ignoreCase = true) ||
                message.contains("connection", ignoreCase = true)

            if (isNetworkIssue && onEnterOffline != null) {
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = onEnterOffline,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error
                    ),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(
                        imageVector = Icons.Default.WifiOff,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Continue in Offline Mode (دخول أوفلاين)",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }
            }
        }
    }
}

@Composable
fun OfflineAdvisoryCard(
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFFFFF8E1)
        )
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = "Offline Operation Mode",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFE65100)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Initial login requires network access to obtain a cryptographically signed JWT. If you previously signed in, your valid session will be restored automatically without network access.",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF8D4004)
            )
        }
    }
}
