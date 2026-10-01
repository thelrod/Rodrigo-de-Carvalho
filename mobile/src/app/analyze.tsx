import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, ScrollView, Image, ActivityIndicator, Alert, TouchableOpacity, KeyboardAvoidingView, Platform, SafeAreaView } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import axios from 'axios';
import * as Sharing from 'expo-sharing';
import { Paths, File } from 'expo-file-system';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.100.4:8000/api/v1';

export default function AnalyzeScreen() {
    const { uri } = useLocalSearchParams<{ uri: string }>();
    const [mode, setMode] = useState<'colony' | 'spot'>('colony');
    const [medium, setMedium] = useState('YPD');
    const [strainId, setStrainId] = useState('BY4741');
    const [plateId, setPlateId] = useState('Plate 15');

    // Parameters
    const [inocVol, setInocVol] = useState('0.1');
    const [dilFactor, setDilFactor] = useState('1000');
    const [gridRows, setGridRows] = useState('4');
    const [gridCols, setGridCols] = useState('6');

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [apiUrl, setApiUrl] = useState(API_URL);
    const [showConfig, setShowConfig] = useState(false);
    const [showOverlay, setShowOverlay] = useState(true);

    const handleAnalyze = async () => {
        if (!uri) {
            Alert.alert('Error', 'No image URI provided.');
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const formData = new FormData();
            formData.append('file', { uri, name: 'upload.jpg', type: 'image/jpeg' } as any);
            formData.append('medium', medium);
            formData.append('strain_id', strainId);
            formData.append('plate_id', plateId);

            let endpoint = '';
            if (mode === 'colony') {
                endpoint = `${apiUrl}/colony-count`;
                formData.append('inoc_vol', inocVol.replace(',', '.'));
                formData.append('dil_factor', dilFactor.replace(',', '.'));
            } else {
                endpoint = `${apiUrl}/spot-assay`;
                formData.append('grid_rows', gridRows.replace(',', '.'));
                formData.append('grid_cols', gridCols.replace(',', '.'));
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData,
            });

            if (!response.ok) {
                const errJson = await response.json().catch(() => null);
                const detail = errJson?.detail || `Server status ${response.status}`;
                throw new Error(detail);
            }

            const data = await response.json();
            setResult(data);
        } catch (error: any) {
            console.error(error);
            const errorMessage = error.message || 'Unknown error occurred.';
            Alert.alert('Analysis Failed', typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
        } finally {
            setLoading(false);
        }
    };

    const handleExportCSV = async () => {
        if (!result?.csv_data) { Alert.alert('Error', 'No data to export.'); return; }
        try {
            const file = new File(Paths.document, `export_${Date.now()}.csv`);
            await file.write(result.csv_data, { encoding: 'utf8' });
            if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(file.uri);
        } catch (error: any) {
            Alert.alert('Export Failed', error.message);
        }
    };

    const handleShareImage = async () => {
        if (!result?.annotated_image_base64) { Alert.alert('Error', 'No image to share.'); return; }
        try {
            const file = new File(Paths.document, `annotated_${Date.now()}.png`);
            await file.write(result.annotated_image_base64, { encoding: 'base64' });
            if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(file.uri);
        } catch (error: any) {
            Alert.alert('Export Failed', error.message);
        }
    };

    const formatCFU = (cfu: number) => {
        if (cfu >= 1000) return cfu.toExponential(2).replace('e+', ' × 10^');
        return `${cfu}`;
    };

    return (
        <SafeAreaView style={styles.safeArea}>
            <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === "ios" ? "padding" : "height"}>

                {/* Top Bar */}
                <View style={styles.topBar}>
                    <TouchableOpacity style={styles.iconButton} onPress={() => router.back()}>
                        <Text style={styles.iconText}>‹</Text>
                    </TouchableOpacity>
                    <Text style={styles.topBarTitle}>{plateId}</Text>
                    <TouchableOpacity style={styles.iconButton} onPress={() => setShowConfig(!showConfig)}>
                        <Text style={styles.iconText}>⚙️</Text>
                    </TouchableOpacity>
                </View>

                <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">

                    {/* Server Configuration (Quick Switch) */}
                    {showConfig && (
                        <View style={styles.configContainer}>
                            <Text style={styles.label}>Backend Server URL:</Text>
                            <TextInput
                                style={styles.input}
                                value={apiUrl}
                                onChangeText={setApiUrl}
                                autoCapitalize="none"
                                autoCorrect={false}
                                placeholder="http://192.168.100.4:8000/api/v1"
                            />
                        </View>
                    )}

                    {/* Count Banner (Colony Mode) */}
                    {mode === 'colony' && result && (
                        <View style={styles.countBanner}>
                            <Text style={styles.countText}>
                                Count: {result.result?.total_colonies_final}
                            </Text>
                            <View style={styles.cfuBadge}>
                                <Text style={styles.cfuBadgeText}>CFU</Text>
                            </View>
                        </View>
                    )}

                    {/* Image Viewport */}
                    {uri && (
                        <View style={styles.viewportContainer}>
                            <Image
                                source={{ uri: (showOverlay && result?.annotated_image_base64) ? `data:image/png;base64,${result.annotated_image_base64}` : uri }}
                                style={styles.viewportImage}
                            />
                            <TouchableOpacity style={styles.fabTopRight} onPress={() => setShowOverlay(!showOverlay)}>
                                <Text style={styles.fabIcon}>👁️</Text>
                            </TouchableOpacity>
                            <TouchableOpacity style={styles.fabBottomLeft}>
                                <Text style={styles.fabIcon}>›</Text>
                            </TouchableOpacity>
                        </View>
                    )}

                    {/* Lab Toolbar */}
                    <View style={styles.toolbar}>
                        {['✂️', '✏️', '➕', '➖', '🎨'].map((icon, idx) => (
                            <TouchableOpacity key={idx} style={styles.toolButton}>
                                <Text style={styles.toolIconText}>{icon}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {/* Mode Selection */}
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

                    {/* Settings Form */}
                    <View style={styles.formContainer}>
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

                        {mode === 'colony' ? (
                            <View style={styles.rowInputs}>
                                <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
                                    <Text style={styles.label}>Inoc. Vol (mL):</Text>
                                    <TextInput style={styles.input} value={inocVol} onChangeText={setInocVol} keyboardType="numeric" />
                                </View>
                                <View style={[styles.inputGroup, { flex: 1 }]}>
                                    <Text style={styles.label}>Dilution (10^x):</Text>
                                    <TextInput style={styles.input} value={dilFactor} onChangeText={setDilFactor} keyboardType="numeric" />
                                </View>
                            </View>
                        ) : (
                            <View style={styles.rowInputs}>
                                <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
                                    <Text style={styles.label}>Rows:</Text>
                                    <TextInput style={styles.input} value={gridRows} onChangeText={setGridRows} keyboardType="numeric" />
                                </View>
                                <View style={[styles.inputGroup, { flex: 1 }]}>
                                    <Text style={styles.label}>Cols:</Text>
                                    <TextInput style={styles.input} value={gridCols} onChangeText={setGridCols} keyboardType="numeric" />
                                </View>
                            </View>
                        )}
                    </View>

                    <TouchableOpacity style={styles.analyzeButton} onPress={handleAnalyze} disabled={loading}>
                        <Text style={styles.analyzeButtonText}>{loading ? 'Analyzing...' : 'Run Analysis'}</Text>
                    </TouchableOpacity>

                    {loading && <ActivityIndicator size="large" color="#1E1E1E" style={{ marginTop: 20 }} />}

                    {/* Results Area */}
                    {result && (
                        <View style={styles.resultsWrapper}>
                            {/* QC Cards */}
                            <View style={styles.qcCardsContainer}>
                                <View style={[styles.qcCard, result.qc?.status === 'passed' ? {backgroundColor: '#E2F9E8'} : {backgroundColor: '#FFE5E5'}]}>
                                    <Text style={styles.qcCardTitle}>QC Status</Text>
                                    <Text style={styles.qcCardValue}>{result.qc?.status === 'passed' ? 'PASS' : 'WARN'}</Text>
                                </View>
                                <View style={styles.qcCard}>
                                    <Text style={styles.qcCardTitle}>Focus</Text>
                                    <Text style={styles.qcCardValue}>{result.qc?.blur_score_laplacian?.toFixed(0)}</Text>
                                </View>
                                <View style={styles.qcCard}>
                                    <Text style={styles.qcCardTitle}>Sat.</Text>
                                    <Text style={styles.qcCardValue}>{(result.qc?.fraction_saturated_pixels * 100).toFixed(1)}%</Text>
                                </View>
                            </View>

                            {result.qc?.rejection_reasons?.length > 0 && (
                                <View style={styles.qcWarningContainer}>
                                    <Text style={styles.qcWarningText}>⚠️ {result.qc.rejection_reasons.join(', ')}</Text>
                                </View>
                            )}

                            {mode === 'colony' ? (
                                <View style={styles.metricsContainer}>
                                    <View style={styles.metricRow}>
                                        <Text style={styles.metricLabel}>ISO 7218 (30-300):</Text>
                                        <View style={[styles.badge, result.result?.is_in_valid_counting_range ? styles.badgeSuccess : styles.badgeError]}>
                                            <Text style={styles.badgeText}>{result.result?.is_in_valid_counting_range ? 'VALID' : 'INVALID'}</Text>
                                        </View>
                                    </View>
                                    {result.result?.cfu_per_ml !== undefined && result.result?.cfu_per_ml !== null && (
                                        <View style={styles.metricRow}>
                                            <Text style={styles.metricLabel}>Concentration:</Text>
                                            <Text style={styles.metricValueLarge}>{formatCFU(result.result.cfu_per_ml)} <Text style={{fontSize: 14}}>CFU/mL</Text></Text>
                                        </View>
                                    )}
                                </View>
                            ) : (
                                <View style={styles.metricsContainer}>
                                    <Text style={styles.metricLabel}>Max Dilution with Growth:</Text>
                                    {Object.entries(result.result?.max_dilution_with_growth_by_strain || {}).map(([strain, dilution]) => (
                                        <View key={strain} style={styles.metricRow}>
                                            <Text style={styles.metricLabel}>{strain}:</Text>
                                            <Text style={styles.metricValue}>
                                                {Number(dilution) > 1 ? `10⁻${Math.round(Math.log10(Number(dilution)))}` : (Number(dilution) === 1 ? '1 (Puro)' : 'None')}
                                            </Text>
                                        </View>
                                    ))}
                                </View>
                            )}

                            {/* Actions */}
                            <View style={styles.actionRow}>
                                <TouchableOpacity style={styles.actionButton} onPress={handleExportCSV}>
                                    <Text style={styles.actionButtonText}>📄 Export CSV</Text>
                                </TouchableOpacity>
                                <TouchableOpacity style={[styles.actionButton, {backgroundColor: '#D8EEF8'}]} onPress={handleShareImage}>
                                    <Text style={styles.actionButtonText}>🖼️ Share Image</Text>
                            </View>
                        </View>
                    )}

                    <View style={{ alignItems: 'center', marginTop: 32, marginBottom: 12 }}>
                        <Text style={{ fontSize: 12, color: '#888', fontWeight: '600' }}>YeastPlate Mobile v1.1.0</Text>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: '#F8F9FA',
    },
    container: {
        flex: 1,
    },
    scrollContent: {
        padding: 20,
        paddingBottom: 40,
    },
    topBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 12,
        backgroundColor: '#F8F9FA',
        borderBottomWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    iconButton: {
        width: 40,
        height: 40,
        borderRadius: 12,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
    },
    iconText: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1E1E1E',
        lineHeight: 24,
    },
    topBarTitle: {
        fontSize: 20,
        fontWeight: '800',
        color: '#1E1E1E',
    },
    countBanner: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#D4F4DD',
        borderRadius: 16,
        borderWidth: 1.5,
        borderColor: '#15803D',
        padding: 16,
        marginBottom: 20,
    },
    countText: {
        fontSize: 24,
        fontWeight: '900',
        color: '#15803D',
    },
    cfuBadge: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderWidth: 1.5,
        borderColor: '#15803D',
    },
    cfuBadgeText: {
        fontSize: 14,
        fontWeight: '800',
        color: '#15803D',
    },
    viewportContainer: {
        width: '100%',
        aspectRatio: 1,
        borderRadius: 20,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        overflow: 'hidden',
        backgroundColor: '#000',
        marginBottom: 16,
        position: 'relative',
    },
    viewportImage: {
        width: '100%',
        height: '100%',
        resizeMode: 'cover',
    },
    fabTopRight: {
        position: 'absolute',
        top: 12,
        right: 12,
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#FFFFFF',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        justifyContent: 'center',
        alignItems: 'center',
    },
    fabBottomLeft: {
        position: 'absolute',
        bottom: 12,
        left: 12,
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#FFFFFF',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        justifyContent: 'center',
        alignItems: 'center',
    },
    fabIcon: {
        fontSize: 20,
    },
    toolbar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 24,
    },
    toolButton: {
        width: 48,
        height: 48,
        borderRadius: 14,
        backgroundColor: '#FFFFFF',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        justifyContent: 'center',
        alignItems: 'center',
    },
    toolIconText: {
        fontSize: 20,
    },
    modeContainer: {
        flexDirection: 'row',
        marginBottom: 20,
        backgroundColor: '#FFFFFF',
        borderRadius: 16,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        padding: 4,
    },
    modeButton: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 12,
    },
    modeButtonActive: {
        backgroundColor: '#D8C4F8',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    modeButtonText: {
        fontWeight: '800',
        color: '#666',
    },
    modeButtonTextActive: {
        color: '#1E1E1E',
    },
    formContainer: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: 16,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        marginBottom: 20,
    },
    inputGroup: {
        marginBottom: 12,
    },
    rowInputs: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    label: {
        fontSize: 14,
        fontWeight: '800',
        color: '#1E1E1E',
        marginBottom: 6,
    },
    input: {
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        borderRadius: 12,
        padding: 12,
        backgroundColor: '#F8F9FA',
        fontSize: 16,
        fontWeight: '600',
    },
    chipContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between'
    },
    chip: {
        flex: 1,
        paddingVertical: 10,
        marginHorizontal: 4,
        borderRadius: 12,
        backgroundColor: '#F8F9FA',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        alignItems: 'center',
    },
    chipActive: {
        backgroundColor: '#1E1E1E',
    },
    chipText: {
        color: '#1E1E1E',
        fontSize: 14,
        fontWeight: '800',
    },
    chipTextActive: {
        color: '#FFFFFF',
    },
    analyzeButton: {
        backgroundColor: '#1E1E1E',
        padding: 18,
        borderRadius: 16,
        alignItems: 'center',
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    analyzeButtonText: {
        color: '#FFFFFF',
        fontWeight: '900',
        fontSize: 18,
    },
    resultsWrapper: {
        marginTop: 24,
    },
    qcCardsContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 16,
    },
    qcCard: {
        flex: 1,
        backgroundColor: '#FFFFFF',
        padding: 12,
        borderRadius: 16,
        marginHorizontal: 4,
        alignItems: 'center',
        borderWidth: 1.5,
        borderColor: '#1E1E1E'
    },
    qcCardTitle: {
        fontSize: 11,
        fontWeight: '800',
        color: '#666',
        marginBottom: 4,
    },
    qcCardValue: {
        fontSize: 16,
        fontWeight: '900',
        color: '#1E1E1E',
    },
    qcWarningContainer: {
        marginBottom: 16,
        padding: 12,
        backgroundColor: '#FFFBE6',
        borderWidth: 1.5,
        borderColor: '#F5C200',
        borderRadius: 12,
    },
    qcWarningText: {
        color: '#A07D00',
        fontWeight: '700',
    },
    metricsContainer: {
        marginBottom: 24,
        backgroundColor: '#FFFFFF',
        padding: 20,
        borderRadius: 20,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    metricRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    metricLabel: {
        fontSize: 16,
        fontWeight: '800',
        color: '#1E1E1E',
    },
    metricValue: {
        fontSize: 18,
        fontWeight: '900',
        color: '#1E1E1E',
    },
    metricValueLarge: {
        fontSize: 24,
        fontWeight: '900',
        color: '#15803D',
    },
    badge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 8,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    badgeSuccess: {
        backgroundColor: '#D4F4DD',
    },
    badgeError: {
        backgroundColor: '#FFE5E5',
    },
    badgeText: {
        fontSize: 12,
        fontWeight: '900',
        color: '#1E1E1E',
    },
    actionRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    actionButton: {
        flex: 1,
        backgroundColor: '#DCF856',
        padding: 16,
        borderRadius: 16,
        alignItems: 'center',
        marginHorizontal: 4,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
    },
    actionButtonText: {
        color: '#1E1E1E',
        fontWeight: '900',
        fontSize: 16,
    },
    configContainer: {
        backgroundColor: '#FFFFFF',
        borderRadius: 16,
        padding: 16,
        borderWidth: 1.5,
        borderColor: '#1E1E1E',
        marginBottom: 16,
    }
});
