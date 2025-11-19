package com.example.datomate.Views

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.example.datomate.Components.*
import com.example.datomate.Navigation.Screen
import com.example.datomate.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportsView(
    navController: NavController
) {
    // Datos de ejemplo (reutilizando los de SummaryView, pero podrías tener muchos más)
    val sampleRecords = listOf(
        DailyRecord("30/11/25", "20ºC", "81%", "12 cm", "12 cm", "20"),
        DailyRecord("29/11/25", "10ºC", "73%", "12 cm", "12 cm"),
        DailyRecord("28/11/25", "20ºC", "64%", "12 cm", "12 cm"),
        DailyRecord("27/11/25", "10ºC", "79%", "12 cm", "12 cm"),
        DailyRecord("26/11/25", "18ºC", "84%", "12 cm", "12 cm")
    )

    var currentScreen by remember { mutableStateOf(Screen.Reports.route) }

    val navItems = listOf(
        BottomNavItem(R.drawable.home, Screen.Home.route),
        BottomNavItem(R.drawable.captura, Screen.DataEntry.route),
        BottomNavItem(R.drawable.prediccion, Screen.Summary.route),
        BottomNavItem(R.drawable.reportes, Screen.Reports.route), // Ícono del archivo es la vista actual
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
                        popUpTo(navController.graph.startDestinationId) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    ) { paddingValues ->
        // 🟢 Cuerpo principal con LazyColumn
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp),
            contentPadding = PaddingValues(top = 16.dp, bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 1. Tarjeta de Historial/Registros (Similar a DataRecordsTable pero con otro título)
            item {
                ReportDataRecordsTable(records = sampleRecords)
            }

            // 2. Tarjeta de Gráfica
            item {
                ChartCard(records = sampleRecords) // 🟢 PASAR LOS DATOS AQUÍ
            }
        }
    }
}

// 📌 Componente auxiliar que reutiliza la estructura de la tabla con diferente título
@Composable
fun ReportDataRecordsTable(
    records: List<DailyRecord>,
    modifier: Modifier = Modifier
) {
    Card(
        shape = RoundedCornerShape(10.dp),
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color.White)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Título Modificado
            Text(
                "Historial", // Título de la imagen: Historial
                style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                modifier = Modifier.padding(bottom = 8.dp)
            )
            Text(
                "Registros", // Subtítulo
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Contenido de la tabla (reutilizando la lógica RecordRow de Components/BodyComponents.kt)
            RecordRow(
                record = DailyRecord("Fecha", "Temperatura", "Humedad", "Longitud", "Diametro"),
                isHeader = true
            )
            Divider(color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f), thickness = 1.dp)

            records.forEachIndexed { index, record ->
                RecordRow(record = record)
                if (index < records.size - 1) {
                    Divider(color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.1f), thickness = 0.5.dp)
                }
            }
        }
    }
}