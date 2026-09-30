import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, ScrollView, Image, ActivityIndicator, Alert, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import axios from 'axios';
import * as Sharing from 'expo-sharing';
import * as FileSystemLegacy from 'expo-file-system/legacy';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.2.2:8000/api/v1';

export default function AnalyzeScreen() {
    const { uri } = useLocalSearchParams<{ uri: string }>();
    const [mode, setMode] = useState<'colony' | 'spot'>('colony');
    const [medium, setMedium] = useState('YPD');
    const [strainId, setStrainId] = useState('BY4741');
    const [plateId, setPlateId] = useState('PLACA_01');

    // Mode 1 specific
    const [inocVol, setInocVol] = useState('0.1');
    const [dilFactor, setDilFactor] = useState('1000');

    // Mode 2 specific
    const [gridRows, setGridRows] = useState('4');
    const [gridCols, setGridCols] = useState('6');

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleAnalyze = async () => {
        if (!uri) {
            Alert.alert('Error', 'No image URI provided.');
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const formData = new FormData();
            formData.append('file', {
                uri,
                name: 'upload.jpg',
                type: 'image/jpeg',
            } as any);

            formData.append('medium', medium);
            formData.append('strain_id', strainId);
            formData.append('plate_id', plateId);

            let endpoint = '';
            if (mode === 'colony') {
                endpoint = `${API_URL}/colony-count`;
                // Replace comma with dot for Portuguese keyboards
                formData.append('inoc_vol', inocVol.replace(',', '.'));
                formData.append('dil_factor', dilFactor.replace(',', '.'));
            } else {
                endpoint = `${API_URL}/spot-assay`;
                formData.append('grid_rows', gridRows.replace(',', '.'));
                formData.append('grid_cols', gridCols.replace(',', '.'));
            }

            const response = await axios.post(endpoint, formData, {
                headers: {
                    'Accept': 'application/json',
                },
            });

            setResult(response.data);

        } catch (error: any) {
            console.error(error);
            const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred.';
            Alert.alert('Analysis Failed', typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        } finally {
            setLoading(false);
        }
    };

    const handleExportCSV = async () => {
        if (!result || !result.csv_data) {
            Alert.alert('Error', 'No data to export.');
            return;
        }

        try {
            const fileUri = `${FileSystemLegacy.documentDirectory}export_${Date.now()}.csv`;
            await FileSystemLegacy.writeAsStringAsync(fileUri, result.csv_data, { encoding: 'utf8' });

            if (await Sharing.isAvailableAsync()) {
                await Sharing.shareAsync(fileUri);
            } else {
                Alert.alert('Warning', 'Sharing is not available on this device.');
            }
        } catch (error: any) {
            console.error(error);
            Alert.alert('Export Failed', error.message);
        }
    };

    const handleShareImage = async () => {
        if (!result || !result.annotated_image_base64) {
            Alert.alert('Error', 'No image to share.');
            return;
        }

        try {
            const fileUri = `${FileSystemLegacy.documentDirectory}annotated_${Date.now()}.png`;
            await FileSystemLegacy.writeAsStringAsync(fileUri, result.annotated_image_base64, { encoding: 'base64' });

            if (await Sharing.isAvailableAsync()) {
                await Sharing.shareAsync(fileUri);
            } else {
                Alert.alert('Warning', 'Sharing is not available on this device.');
            }
        } catch (error: any) {
            console.error(error);
            Alert.alert('Export Failed', error.message);
        }
    }

    const formatCFU = (cfu: number) => {
        if (cfu >= 1000) {
            return cfu.toExponential(2).replace('e+', ' × 10^') + ' UFC/mL';
        }
        return `${cfu} UFC/mL`;
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
            <ScrollView contentContainerStyle={{ padding: 20 }} keyboardShouldPersistTaps="handled">
                {uri && (
                    <Image source={{ uri }} style={styles.previewImage} />
                )}

                <View style={styles.modeContainer}>
                    <TouchableOpacity
                        style={[styles.modeButton, mode === 'colony' && styles.modeButtonActive]}
                        onPress={() => setMode('colony')}
                    >
                        <Text style={[styles.modeButtonText, mode === 'colony' && styles.modeButtonTextActive]}>Colony Count</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.modeButton, mode === 'spot' && styles.modeButtonActive]}
                        onPress={() => setMode('spot')}
                    >
                        <Text style={[styles.modeButtonText, mode === 'spot' && styles.modeButtonTextActive]}>Spot Assay</Text>
                    </TouchableOpacity>
                </View>

                <View style={styles.inputGroup}>
                    <Text style={styles.label}>Medium:</Text>
                    <View style={styles.chipContainer}>
                        {['YPD', 'YPGal', 'YPGly'].map((m) => (
                            <TouchableOpacity
                                key={m}
                                style={[styles.chip, medium === m && styles.chipActive]}
                                onPress={() => setMedium(m)}
                            >
                                <Text style={[styles.chipText, medium === m && styles.chipTextActive]}>{m}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
                <View style={styles.inputGroup}>
                    <Text style={styles.label}>Strain ID:</Text>
                    <TextInput style={styles.input} value={strainId} onChangeText={setStrainId} />
                </View>
                <View style={styles.inputGroup}>
                    <Text style={styles.label}>Plate ID:</Text>
                    <TextInput style={styles.input} value={plateId} onChangeText={setPlateId} />
                </View>

                {mode === 'colony' ? (
                    <>
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Inoculated Vol (mL):</Text>
                            <TextInput style={styles.input} value={inocVol} onChangeText={setInocVol} keyboardType="numeric" />
                        </View>
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Dilution Factor:</Text>
                            <TextInput style={styles.input} value={dilFactor} onChangeText={setDilFactor} keyboardType="numeric" />
                        </View>
                    </>
                ) : (
                    <>
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Grid Rows:</Text>
                            <TextInput style={styles.input} value={gridRows} onChangeText={setGridRows} keyboardType="numeric" />
                        </View>
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Grid Cols:</Text>
                            <TextInput style={styles.input} value={gridCols} onChangeText={setGridCols} keyboardType="numeric" />
                        </View>
                    </>
                )}

                <TouchableOpacity style={styles.analyzeButton} onPress={handleAnalyze} disabled={loading}>
                    <Text style={styles.analyzeButtonText}>Analyze</Text>
                </TouchableOpacity>

                {loading && <ActivityIndicator size="large" color="#007bff" style={{ marginTop: 20 }} />}

                {result && (
                    <View style={styles.resultsContainer}>
                        <Text style={styles.resultTitle}>Results</Text>

                        <View style={styles.qcCardsContainer}>
                            <View style={styles.qcCard}>
                                <Text style={styles.qcCardTitle}>QC Status</Text>
                                <Text style={[styles.qcCardValue, result.qc?.status === 'passed' ? {color: 'green'} : {color: 'orange'}]}>{result.qc?.status}</Text>
                            </View>
                            <View style={styles.qcCard}>
                                <Text style={styles.qcCardTitle}>Focus (Laplacian)</Text>
                                <Text style={styles.qcCardValue}>{result.qc?.blur_score_laplacian?.toFixed(1)}</Text>
                            </View>
                            <View style={styles.qcCard}>
                                <Text style={styles.qcCardTitle}>Saturation</Text>
                                <Text style={styles.qcCardValue}>{(result.qc?.fraction_saturated_pixels * 100).toFixed(1)}%</Text>
                            </View>
                             <View style={styles.qcCard}>
                                <Text style={styles.qcCardTitle}>Plate Visible</Text>
                                <Text style={styles.qcCardValue}>{result.qc?.is_plate_fully_visible ? 'Yes' : 'No'}</Text>
                            </View>
                        </View>

                        {result.qc?.rejection_reasons?.length > 0 && (
                            <View style={styles.qcWarningContainer}>
                                <Text style={styles.qcWarning}>Warnings: {result.qc.rejection_reasons.join(', ')}</Text>
                            </View>
                        )}

                        {mode === 'colony' ? (
                            <View style={styles.metricsContainer}>
                                <View style={styles.metricRow}>
                                    <Text style={styles.metricLabel}>Total Colonies:</Text>
                                    <Text style={styles.metricValue}>{result.result?.total_colonies_final}</Text>
                                </View>
                                <View style={styles.metricRow}>
                                    <Text style={styles.metricLabel}>ISO 7218 (30-300):</Text>
                                    <View style={[styles.badge, result.result?.is_in_valid_counting_range ? styles.badgeSuccess : styles.badgeError]}>
                                        <Text style={styles.badgeText}>{result.result?.is_in_valid_counting_range ? 'VALID' : 'INVALID'}</Text>
                                    </View>
                                </View>
                                {result.result?.cfu_per_ml !== undefined && result.result?.cfu_per_ml !== null && (
                                    <View style={styles.metricRow}>
                                        <Text style={styles.metricLabel}>CFU/mL:</Text>
                                        <Text style={styles.metricValue}>{formatCFU(result.result.cfu_per_ml)}</Text>
                                    </View>
                                )}
                            </View>
                        ) : (
                            <View style={styles.metricsContainer}>
                                <Text style={styles.metricLabel}>Max Dilution with Growth:</Text>
                                {Object.entries(result.result?.max_dilution_with_growth_by_strain || {}).map(([strain, dilution]) => (
                                    <View key={strain} style={styles.metricRow}>
                                        <Text>{strain}:</Text>
                                        <Text style={styles.metricValue}>
                                            {Number(dilution) > 1 ? `10⁻${Math.round(Math.log10(Number(dilution)))}` : (Number(dilution) === 1 ? '1 (Puro)' : 'Nenhum Crescimento')}
                                        </Text>
                                    </View>
                                ))}
                            </View>
                        )}

                        {result.annotated_image_base64 && (
                            <Image
                                source={{ uri: `data:image/png;base64,${result.annotated_image_base64}` }}
                                style={styles.resultImage}
                            />
                        )}

                        <View style={styles.exportContainer}>
                            <TouchableOpacity style={styles.exportButton} onPress={handleExportCSV}>
                                <Text style={styles.exportText}>Export CSV</Text>
                            </TouchableOpacity>
                             <TouchableOpacity style={[styles.exportButton, {backgroundColor: '#17a2b8'}]} onPress={handleShareImage}>
                                <Text style={styles.exportText}>Share Image</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                )}
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    previewImage: {
        width: '100%',
        height: 200,
        resizeMode: 'cover',
        borderRadius: 10,
        marginBottom: 20,
    },
    modeContainer: {
        flexDirection: 'row',
        marginBottom: 20,
        backgroundColor: '#e0e0e0',
        borderRadius: 8,
        padding: 4,
    },
    modeButton: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 6,
    },
    modeButtonActive: {
        backgroundColor: 'white',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    modeButtonText: {
        fontWeight: 'bold',
        color: '#666',
    },
    modeButtonTextActive: {
        color: '#007bff',
    },
    inputGroup: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 15,
    },
    label: {
        flex: 1,
        fontSize: 16,
        fontWeight: 'bold',
    },
    input: {
        flex: 2,
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 5,
        padding: 10,
        backgroundColor: 'white',
    },
    chipContainer: {
        flex: 2,
        flexDirection: 'row',
        justifyContent: 'space-between'
    },
    chip: {
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 16,
        backgroundColor: '#e0e0e0',
    },
    chipActive: {
        backgroundColor: '#007bff',
    },
    chipText: {
        color: '#333',
        fontSize: 14,
    },
    chipTextActive: {
        color: 'white',
        fontWeight: 'bold',
    },
    analyzeButton: {
        backgroundColor: '#007bff',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 10,
    },
    analyzeButtonText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 18,
    },
    resultsContainer: {
        marginTop: 30,
        padding: 15,
        backgroundColor: 'white',
        borderRadius: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 5,
        elevation: 3,
    },
    resultTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 15,
        textAlign: 'center',
    },
    qcCardsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        marginBottom: 10,
    },
    qcCard: {
        width: '48%',
        backgroundColor: '#f8f9fa',
        padding: 10,
        borderRadius: 8,
        marginBottom: 10,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#eee'
    },
    qcCardTitle: {
        fontSize: 12,
        color: '#666',
        marginBottom: 4,
    },
    qcCardValue: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333',
    },
    qcWarningContainer: {
        marginBottom: 15,
        padding: 10,
        backgroundColor: '#fff3cd',
        borderLeftWidth: 4,
        borderLeftColor: '#ffc107',
        borderRadius: 4,
    },
    qcWarning: {
        color: '#856404',
    },
    metricsContainer: {
        marginBottom: 15,
        backgroundColor: '#f8f9fa',
        padding: 15,
        borderRadius: 8,
    },
    metricRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    metricLabel: {
        fontSize: 16,
        fontWeight: '600',
        color: '#555',
    },
    metricValue: {
        fontSize: 16,
        fontWeight: 'bold',
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    badgeSuccess: {
        backgroundColor: '#d4edda',
    },
    badgeError: {
        backgroundColor: '#f8d7da',
    },
    badgeText: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#333',
    },
    resultImage: {
        width: '100%',
        height: 300,
        resizeMode: 'contain',
        marginVertical: 15,
    },
    exportContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 10,
    },
    exportButton: {
        flex: 1,
        backgroundColor: '#28a745',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginHorizontal: 5,
    },
    exportText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    }
});
