package com.example.datomate.Views

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.example.datomate.Components.*
import com.example.datomate.Navigation.Screen
import com.example.datomate.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SummaryView(navController: NavController) {

    // Estado para la navegación inferior
    var currentScreen by remember { mutableStateOf(Screen.Summary.route) }

    // Definición de los ítems de la barra inferior
    val navItems = listOf(
        BottomNavItem(R.drawable.home, Screen.Home.route),
        BottomNavItem(R.drawable.captura, Screen.DataEntry.route),
        BottomNavItem(R.drawable.prediccion, Screen.Summary.route),
        BottomNavItem(R.drawable.reportes, Screen.Reports.route),
        BottomNavItem(R.drawable.imagenes, "image"),
        BottomNavItem(R.drawable.perfil, Screen.Profile.route)
    )

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,

        topBar = {
            TopAppBar(
                title = { AppLogoBar(100, Alignment.TopStart) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = Color.White
                )
            )
        },

        bottomBar = {
            BottomNavBar(
                items = navItems,
                currentRoute = currentScreen,
                onItemSelected = { route ->
                    currentScreen = route
                    navController.navigate(route) {
                        // Esto evita múltiples instancias de la misma pantalla
                        popUpTo(navController.graph.startDestinationId) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    ) { paddingValues ->
        // Cuerpo principal con scroll
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp)
                .padding(top = 16.dp) // Espacio adicional después de la TopBar
        ) {
            ContenteSummaryView()
        }
    }
}

@Composable
fun ContenteSummaryView(){
    // Datos de ejemplo para la tabla (5 registros)
    val sampleRecords = listOf(
        DailyRecord("30/11/25", "20ºC", "81%", "12 cm", "12 cm"),
        DailyRecord("29/11/25", "10ºC", "73%", "12 cm", "12 cm"),
        DailyRecord("28/11/25", "20ºC", "64%", "12 cm", "12 cm"),
        DailyRecord("27/11/25", "10ºC", "79%", "12 cm", "12 cm"),
        DailyRecord("26/11/25", "18ºC", "84%", "12 cm", "12 cm")
    )

    // Tarjeta de Registros
    DataRecordsTable(
        records = sampleRecords,
        modifier = Modifier.padding(bottom = 16.dp)
    )

    // Tarjeta de Predicción
    PredictionCard(
        title = "Predicción del siguiente día.",
        predictionResult = "Peso del racimo: 20 kg"
    )
}