import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, ScrollView, Image, ActivityIndicator, Alert, TouchableOpacity } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import axios from 'axios';
import * as Sharing from 'expo-sharing';
import * as FileSystemLegacy from 'expo-file-system/legacy';
import { Paths, File } from 'expo-file-system';

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
                formData.append('inoc_vol', inocVol);
                formData.append('dil_factor', dilFactor);
            } else {
                endpoint = `${API_URL}/spot-assay`;
                formData.append('grid_rows', gridRows);
                formData.append('grid_cols', gridCols);
            }

            const response = await axios.post(endpoint, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            setResult(response.data);

        } catch (error: any) {
            console.error(error);
            Alert.alert('Analysis Failed', error.message || 'Unknown error occurred.');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        if (!result || !result.csv_data) {
            Alert.alert('Error', 'No data to export.');
            return;
        }

        try {
            const fileUri = `${Paths.document.uri}export_${Date.now()}.csv`;
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

    return (
        <ScrollView style={styles.container} contentContainerStyle={{ padding: 20 }}>
            {uri && (
                <Image source={{ uri }} style={styles.previewImage} />
            )}

            <View style={styles.modeContainer}>
                <Button
                    title="Colony Count"
                    onPress={() => setMode('colony')}
                    color={mode === 'colony' ? '#007bff' : 'gray'}
                />
                <Button
                    title="Spot Assay"
                    onPress={() => setMode('spot')}
                    color={mode === 'spot' ? '#007bff' : 'gray'}
                />
            </View>

            <View style={styles.inputGroup}>
                <Text style={styles.label}>Medium:</Text>
                <TextInput style={styles.input} value={medium} onChangeText={setMedium} />
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

            <Button title="Analyze" onPress={handleAnalyze} disabled={loading} />

            {loading && <ActivityIndicator size="large" color="#0000ff" style={{ marginTop: 20 }} />}

            {result && (
                <View style={styles.resultsContainer}>
                    <Text style={styles.resultTitle}>Results</Text>

                    <View style={styles.qcContainer}>
                        <Text style={styles.qcText}>QC Status: {result.qc?.status}</Text>
                        {result.qc?.rejection_reasons?.length > 0 && (
                            <Text style={styles.qcWarning}>Warnings: {result.qc.rejection_reasons.join(', ')}</Text>
                        )}
                    </View>

                    {mode === 'colony' ? (
                        <View style={styles.metricsContainer}>
                            <Text>Total Colonies: {result.result?.total_colonies_final}</Text>
                            <Text>Valid Range: {result.result?.is_in_valid_counting_range ? 'Yes' : 'No'}</Text>
                            <Text>CFU/mL: {result.result?.cfu_per_ml}</Text>
                        </View>
                    ) : (
                        <View style={styles.metricsContainer}>
                            <Text>Max Dilution with Growth: {result.result?.max_dilution_with_growth_by_strain?.[strainId]}</Text>
                        </View>
                    )}

                    {result.annotated_image_base64 && (
                        <Image
                            source={{ uri: `data:image/png;base64,${result.annotated_image_base64}` }}
                            style={styles.resultImage}
                        />
                    )}

                    <TouchableOpacity style={styles.exportButton} onPress={handleExport}>
                        <Text style={styles.exportText}>Export CSV</Text>
                    </TouchableOpacity>
                </View>
            )}
        </ScrollView>
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
        justifyContent: 'space-around',
        marginBottom: 20,
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
        marginBottom: 10,
        textAlign: 'center',
    },
    qcContainer: {
        marginBottom: 10,
        padding: 10,
        backgroundColor: '#f0f0f0',
        borderRadius: 5,
    },
    qcText: {
        fontWeight: 'bold',
    },
    qcWarning: {
        color: 'red',
        marginTop: 5,
    },
    metricsContainer: {
        marginBottom: 15,
    },
    resultImage: {
        width: '100%',
        height: 300,
        resizeMode: 'contain',
        marginVertical: 15,
    },
    exportButton: {
        backgroundColor: '#28a745',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
    },
    exportText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    }
});
