import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Button, Dimensions } from 'react-native';
import { CameraView, useCameraPermissions, CameraPictureOptions } from 'expo-camera';
import { Accelerometer } from 'expo-sensors';
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const OVERLAY_SIZE = SCREEN_WIDTH * 0.8;

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [levelStatus, setLevelStatus] = useState<'level' | 'tilted'>('tilted');
  const cameraRef = useRef<CameraView>(null);

  useEffect(() => {
    let subscription: any;

    Accelerometer.setUpdateInterval(500);
    subscription = Accelerometer.addListener(data => {
        const { x, y, z } = data;
        // Check if device is held flat. Z should be close to -1 or 1, and X/Y close to 0
        const isFlat = Math.abs(x) < 0.15 && Math.abs(y) < 0.15 && Math.abs(z) > 0.85;
        setLevelStatus(isFlat ? 'level' : 'tilted');
    });

    return () => {
      subscription && subscription.remove();
    };
  }, []);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  const takePicture = async () => {
      if (cameraRef.current) {
          const options: CameraPictureOptions = {
              quality: 1.0,
              base64: false,
              exif: false
          };
          try {
              const photo = await cameraRef.current.takePictureAsync(options);
              if (photo && photo.uri) {
                  router.push({ pathname: '/analyze', params: { uri: photo.uri } });
              }
          } catch(e) {
              console.error("Failed to take picture", e);
          }
      }
  };

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      router.push({ pathname: '/analyze', params: { uri: result.assets[0].uri } });
    }
  };

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} facing={"back"} flash={"off"} ref={cameraRef}>
        <View style={styles.overlayContainer}>
            {/* Guide circle */}
            <View style={[
                styles.guideCircle,
                levelStatus === 'level' ? styles.guideCircleLevel : styles.guideCircleTilted
            ]} />

            <View style={styles.levelIndicatorContainer}>
               <Text style={styles.levelIndicatorText}>
                   {levelStatus === 'level' ? '✅ Perpendicular' : '⚠️ Adjust Angle'}
               </Text>
            </View>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity style={styles.galleryButton} onPress={pickImage}>
             <Text style={styles.text}>Gallery</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
             <View style={styles.captureInner} />
          </TouchableOpacity>
          <View style={{flex: 1}} />
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: 'black'
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
    color: 'white'
  },
  camera: {
    flex: 1,
  },
  overlayContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
  },
  guideCircle: {
      width: OVERLAY_SIZE,
      height: OVERLAY_SIZE,
      borderRadius: OVERLAY_SIZE / 2,
      borderWidth: 3,
      backgroundColor: 'transparent',
  },
  guideCircleTilted: {
      borderColor: 'rgba(255, 204, 0, 0.7)',
  },
  guideCircleLevel: {
      borderColor: 'rgba(0, 255, 0, 0.9)',
  },
  levelIndicatorContainer: {
      marginTop: 20,
      padding: 8,
      backgroundColor: 'rgba(0,0,0,0.5)',
      borderRadius: 10
  },
  levelIndicatorText: {
      color: 'white',
      fontWeight: 'bold',
      fontSize: 16
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 40,
    flexDirection: 'row',
    width: '100%',
    paddingHorizontal: 30,
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  galleryButton: {
      flex: 1,
      alignItems: 'flex-start',
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureInner: {
      width: 56,
      height: 56,
      borderRadius: 28,
      backgroundColor: 'white',
  },
  text: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
  },
});
