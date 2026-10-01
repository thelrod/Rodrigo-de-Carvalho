import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, SafeAreaView, Dimensions, StatusBar } from 'react-native';
import { router } from 'expo-router';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function DashboardScreen() {
  const handleLaunchCamera = () => {
    router.push('/camera');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.container}>

        {/* Header Section */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.searchButton}>
            <Text style={styles.searchIcon}>🔍</Text>
          </TouchableOpacity>
          <View style={styles.headerRight}>
            <Text style={styles.headerSlogan}>Science first, panic later</Text>
            <View style={styles.mascotCircle}>
              <Text style={styles.mascotEmoji}>🧬</Text>
            </View>
          </View>
        </View>

        {/* Tools Carousel */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Lab Tools</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.carouselContainer}>

            {/* Colony Counter Card */}
            <TouchableOpacity style={[styles.toolCard, { backgroundColor: '#D8EEF8' }]} onPress={handleLaunchCamera}>
              <Text style={styles.toolIcon}>🧫</Text>
              <Text style={styles.toolTitle}>Colony Counter</Text>
              <Text style={styles.toolSubtitle}>Spread Plate Analysis</Text>
            </TouchableOpacity>

            {/* Dilution Card */}
            <TouchableOpacity style={[styles.toolCard, { backgroundColor: '#C7E9FB' }]} onPress={handleLaunchCamera}>
              <Text style={styles.toolIcon}>💧</Text>
              <Text style={styles.toolTitle}>Dilution</Text>
              <Text style={styles.toolSubtitle}>Spot Assay Engine</Text>
            </TouchableOpacity>

             {/* Medium Card */}
            <TouchableOpacity style={[styles.toolCard, { backgroundColor: '#D8C4F8' }]}>
              <Text style={styles.toolIcon}>🧪</Text>
              <Text style={styles.toolTitle}>Medium Prep</Text>
              <Text style={styles.toolSubtitle}>Recipes & Stock</Text>
            </TouchableOpacity>

          </ScrollView>
        </View>

        {/* Protocol Card */}
        <View style={styles.section}>
            <Text style={styles.sectionTitle}>Active Protocol</Text>
            <TouchableOpacity style={styles.protocolCard}>
                <View style={styles.protocolTab} />
                <View style={styles.protocolContent}>
                    <Text style={styles.protocolTitle}>YPGal Stress Screening</Text>
                    <Text style={styles.protocolSubtitle}>In progress - 24h incubation</Text>
                    <View style={styles.progressBarBg}>
                        <View style={styles.progressBarFill} />
                    </View>
                </View>
            </TouchableOpacity>
        </View>

      </ScrollView>

      {/* Floating Bottom Dock */}
      <View style={styles.dockWrapper}>
        <View style={styles.dock}>
            <TouchableOpacity style={[styles.dockIcon, styles.dockIconActive]} onPress={() => router.push('/')}>
                <Text style={styles.iconText}>🏠</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.dockIcon}>
                <Text style={styles.iconText}>📄</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.dockIcon} onPress={handleLaunchCamera}>
                <Text style={styles.iconText}>🎛️</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.dockIcon}>
                <Text style={styles.iconText}>⏱️</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.dockIcon}>
                <Text style={styles.iconText}>⚙️</Text>
            </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  container: {
    padding: 20,
    paddingBottom: 100, // Make room for dock
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
    marginTop: 10,
  },
  searchButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#1E1E1E',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  searchIcon: {
      fontSize: 20,
  },
  headerRight: {
      flexDirection: 'row',
      alignItems: 'center',
  },
  headerSlogan: {
      fontFamily: 'System',
      fontSize: 14,
      fontWeight: '600',
      color: '#666',
      marginRight: 12,
  },
  mascotCircle: {
      width: 48,
      height: 48,
      borderRadius: 24,
      backgroundColor: '#E2F9E8',
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 1.5,
      borderColor: '#1E1E1E',
  },
  mascotEmoji: {
      fontSize: 24,
  },
  section: {
      marginBottom: 32,
  },
  sectionTitle: {
      fontSize: 20,
      fontWeight: '800',
      color: '#1E1E1E',
      marginBottom: 16,
  },
  carouselContainer: {
      paddingBottom: 8,
      paddingRight: 20, // For trailing edge spacing
  },
  toolCard: {
      width: 160,
      height: 200,
      borderRadius: 24,
      padding: 20,
      marginRight: 16,
      borderWidth: 1.5,
      borderColor: '#1E1E1E',
      justifyContent: 'space-between',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 4,
  },
  toolIcon: {
      fontSize: 40,
  },
  toolTitle: {
      fontSize: 20,
      fontWeight: '800',
      color: '#1E1E1E',
      marginTop: 'auto',
  },
  toolSubtitle: {
      fontSize: 12,
      fontWeight: '600',
      color: '#1E1E1E',
      opacity: 0.7,
      marginTop: 4,
  },
  protocolCard: {
      backgroundColor: '#DCF856', // Lime Green
      borderRadius: 24,
      borderTopLeftRadius: 0, // Makes room for the folder tab effect visually
      borderWidth: 1.5,
      borderColor: '#1E1E1E',
      marginTop: 12,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
  },
  protocolTab: {
      position: 'absolute',
      top: -14,
      left: -1.5,
      width: 80,
      height: 16,
      backgroundColor: '#DCF856',
      borderTopLeftRadius: 12,
      borderTopRightRadius: 12,
      borderWidth: 1.5,
      borderBottomWidth: 0,
      borderColor: '#1E1E1E',
  },
  protocolContent: {
      padding: 24,
  },
  protocolTitle: {
      fontSize: 22,
      fontWeight: '800',
      color: '#1E1E1E',
      marginBottom: 4,
  },
  protocolSubtitle: {
      fontSize: 14,
      fontWeight: '600',
      color: '#1E1E1E',
      opacity: 0.8,
      marginBottom: 20,
  },
  progressBarBg: {
      height: 12,
      backgroundColor: 'rgba(30,30,30,0.1)',
      borderRadius: 6,
      overflow: 'hidden',
  },
  progressBarFill: {
      width: '60%',
      height: '100%',
      backgroundColor: '#1E1E1E',
      borderRadius: 6,
  },
  dockWrapper: {
      position: 'absolute',
      bottom: 30,
      left: 0,
      right: 0,
      alignItems: 'center',
  },
  dock: {
      flexDirection: 'row',
      backgroundColor: '#FFFFFF',
      paddingHorizontal: 20,
      paddingVertical: 12,
      borderRadius: 36,
      borderWidth: 1.5,
      borderColor: '#1E1E1E',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.15,
      shadowRadius: 12,
      elevation: 8,
      justifyContent: 'space-between',
      width: SCREEN_WIDTH * 0.85,
  },
  dockIcon: {
      width: 48,
      height: 48,
      justifyContent: 'center',
      alignItems: 'center',
      borderRadius: 24,
  },
  dockIconActive: {
      backgroundColor: '#D8C4F8',
      borderWidth: 1.5,
      borderColor: '#1E1E1E',
  },
  iconText: {
      fontSize: 22,
  },
});
