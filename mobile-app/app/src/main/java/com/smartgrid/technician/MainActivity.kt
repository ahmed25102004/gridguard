package com.smartgrid.technician

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ElectricalServices
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.smartgrid.technician.features.assets.ui.AssetDetailScreen
import com.smartgrid.technician.features.assets.ui.AssetDetailViewModel
import com.smartgrid.technician.features.assets.ui.AssetListScreen
import com.smartgrid.technician.features.assets.ui.AssetListViewModel
import com.smartgrid.technician.features.auth.AuthState
import com.smartgrid.technician.features.auth.AuthViewModel
import com.smartgrid.technician.features.auth.LoginScreen
import com.smartgrid.technician.features.auth.UserSession
import com.smartgrid.technician.ui.theme.AppBackground
import com.smartgrid.technician.ui.theme.AppOutline
import com.smartgrid.technician.ui.theme.AppTextPrimary
import com.smartgrid.technician.ui.theme.ElectricBlue
import com.smartgrid.technician.ui.theme.ElectricBlueContainer
import com.smartgrid.technician.ui.theme.SlateBlue
import com.smartgrid.technician.ui.theme.SmartGridTheme
import com.smartgrid.technician.ui.theme.SuccessGreen
import com.smartgrid.technician.ui.theme.SuccessGreenBorder
import com.smartgrid.technician.ui.theme.SuccessGreenContainer
import com.smartgrid.technician.ui.theme.WarningAmber
import com.smartgrid.technician.ui.theme.WarningAmberContainer
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : ComponentActivity() {

    private val authViewModel: AuthViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                val app = application as SmartGridApplication
                return AuthViewModel(
                    authRepository = app.container.authRepository,
                    connectivityObserver = app.container.connectivityObserver
                ) as T
            }
        }
    }

    private val assetListViewModel: AssetListViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                val app = application as SmartGridApplication
                return AssetListViewModel(
                    assetRepository = app.container.assetRepository,
                    connectivityObserver = app.container.connectivityObserver
                ) as T
            }
        }
    }

    private val assetDetailViewModel: AssetDetailViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                val app = application as SmartGridApplication
                return AssetDetailViewModel(
                    assetRepository = app.container.assetRepository,
                    connectivityObserver = app.container.connectivityObserver
                ) as T
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SmartGridTheme {
                val uiState by authViewModel.uiState.collectAsStateWithLifecycle()

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AnimatedContent(
                        targetState = uiState.authState is AuthState.Authenticated,
                        transitionSpec = { fadeIn() togetherWith fadeOut() },
                        label = "AuthNavigationTransition"
                    ) { isAuthenticated ->
                        if (isAuthenticated && uiState.authState is AuthState.Authenticated) {
                            val authenticatedState = uiState.authState as AuthState.Authenticated

                            var currentDestination by rememberSaveable { mutableStateOf("dashboard") }
                            var activeAssetId by rememberSaveable { mutableStateOf<String?>(null) }

                            when (currentDestination) {
                                "assets" -> {
                                    BackHandler { currentDestination = "dashboard" }
                                    AssetListScreen(
                                        viewModel = assetListViewModel,
                                        onAssetClick = { asset ->
                                            activeAssetId = asset.id
                                            currentDestination = "detail"
                                        },
                                        onBackClick = { currentDestination = "dashboard" }
                                    )
                                }
                                "detail" -> {
                                    BackHandler { currentDestination = "assets" }
                                    AssetDetailScreen(
                                        assetId = activeAssetId ?: "",
                                        viewModel = assetDetailViewModel,
                                        onBackClick = { currentDestination = "assets" }
                                    )
                                }
                                else -> {
                                    TechnicianWorkspaceScreen(
                                        session = authenticatedState.session,
                                        isOffline = authenticatedState.isOffline,
                                        onNavigateToAssets = { currentDestination = "assets" },
                                        onLogout = { authViewModel.logout() }
                                    )
                                }
                            }
                        } else {
                            LoginScreen(viewModel = authViewModel)
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TechnicianWorkspaceScreen(
    session: UserSession,
    isOffline: Boolean,
    onNavigateToAssets: () -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier
) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = AppBackground,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.Bolt,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(22.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Smart Grid Platform",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = ElectricBlue,
                    titleContentColor = Color.White
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // ── PROFILE CARD (Matches Reference Image) ──────────────────
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(58.dp)
                            .clip(CircleShape)
                            .background(ElectricBlueContainer),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = "Technician Avatar",
                            tint = ElectricBlue,
                            modifier = Modifier.size(34.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(14.dp))

                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = session.name,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = AppTextPrimary
                        )
                        Text(
                            text = session.role.replaceFirstChar { it.uppercase() },
                            style = MaterialTheme.typography.bodySmall,
                            fontWeight = FontWeight.Medium,
                            color = SlateBlue
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = session.email,
                            style = MaterialTheme.typography.bodySmall,
                            color = SlateBlue
                        )
                    }

                    Icon(
                        imageVector = Icons.Default.CheckCircle,
                        contentDescription = "Verified Session",
                        tint = SuccessGreen,
                        modifier = Modifier.size(22.dp)
                    )
                }
            }

            // ── ACCESS GRANTED / OPERATIONAL MODE BANNER ────────────────
            val bannerBg = if (isOffline) WarningAmberContainer else SuccessGreenContainer
            val bannerBorder = if (isOffline) WarningAmber.copy(alpha = 0.4f) else SuccessGreenBorder
            val bannerTint = if (isOffline) WarningAmber else SuccessGreen

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                color = bannerBg,
                border = BorderStroke(1.dp, bannerBorder)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                            .background(bannerTint.copy(alpha = 0.14f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = if (isOffline) Icons.Default.WifiOff else Icons.Default.Shield,
                            contentDescription = null,
                            tint = bannerTint,
                            modifier = Modifier.size(22.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(12.dp))

                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = if (isOffline) "Offline Operational Mode" else "Access Granted • Online Synced",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = bannerTint
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = if (isOffline) {
                                "Working locally from AES-256 SQLCipher encrypted cache"
                            } else {
                                "Authenticated technician session active via FastAPI"
                            },
                            style = MaterialTheme.typography.bodySmall,
                            color = bannerTint.copy(alpha = 0.85f)
                        )
                    }
                }
            }

            // ── SUBSTATION ASSET REGISTRY ACTION CARD ───────────────────
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .clickable(onClick = onNavigateToAssets),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(48.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(ElectricBlueContainer),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.ElectricalServices,
                                contentDescription = null,
                                tint = ElectricBlue,
                                modifier = Modifier.size(26.dp)
                            )
                        }
                        Spacer(modifier = Modifier.width(14.dp))
                        Column {
                            Text(
                                text = "Substation Asset Registry",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = AppTextPrimary
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = "Transformers, Circuit Breakers & Cables",
                                style = MaterialTheme.typography.bodySmall,
                                color = SlateBlue
                            )
                        }
                    }
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = "Navigate to Asset Registry",
                        tint = ElectricBlue
                    )
                }
            }

            // ── SECURITY & SESSION STATUS SECTION ───────────────────────
            Text(
                text = "Security & Session Status",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = AppTextPrimary,
                modifier = Modifier.padding(top = 4.dp, start = 2.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    StatusItem(
                        icon = Icons.Default.Lock,
                        title = "Android Keystore Vault",
                        description = "Hardware-backed master key & AES-256-GCM tokens"
                    )

                    StatusItem(
                        icon = Icons.Default.Storage,
                        title = "Local Encrypted Database",
                        description = "SQLCipher AES-256 encrypted SQLite storage"
                    )

                    StatusItem(
                        icon = if (isOffline) Icons.Default.WifiOff else Icons.Default.Wifi,
                        title = "JWT Session Active",
                        description = "Token expires: ${formatTimestamp(session.expiresAt)}"
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // ── LOGOUT ACTION BUTTON ────────────────────────────────────
            OutlinedButton(
                onClick = onLogout,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                shape = RoundedCornerShape(14.dp),
                border = BorderStroke(1.2.dp, MaterialTheme.colorScheme.error.copy(alpha = 0.5f)),
                colors = ButtonDefaults.outlinedButtonColors(
                    containerColor = Color.White,
                    contentColor = MaterialTheme.colorScheme.error
                )
            ) {
                Icon(
                    imageVector = Icons.Default.ExitToApp,
                    contentDescription = "Logout Icon",
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "End Secure Session (Logout)",
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
fun StatusItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    description: String
) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth()
    ) {
        Box(
            modifier = Modifier
                .size(38.dp)
                .clip(CircleShape)
                .background(ElectricBlueContainer),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = ElectricBlue,
                modifier = Modifier.size(20.dp)
            )
        }
        Spacer(modifier = Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = AppTextPrimary
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = SlateBlue
            )
        }
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = null,
            tint = SuccessGreen,
            modifier = Modifier.size(18.dp)
        )
    }
}

private fun formatTimestamp(millis: Long): String {
    return try {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        sdf.format(Date(millis))
    } catch (_: Exception) {
        "$millis"
    }
}
