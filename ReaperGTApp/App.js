// App.js
import React, { useState } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  Image,
  StyleSheet,
  StatusBar,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

// Make sure logo_small.png is in your assets folder
import logo from './assets/logo.png';

export default function App() {
  const [crnInput, setCrnInput] = useState('');
  const [trackedCrns, setTrackedCrns] = useState([]);

  const subscribe = () => {
    const trimmed = crnInput.trim();
    if (trimmed && !trackedCrns.includes(trimmed)) {
      setTrackedCrns([trimmed, ...trackedCrns]);
      setCrnInput('');
    }
  };

  const unsubscribe = (crn) => {
    setTrackedCrns(trackedCrns.filter(item => item !== crn));
  };

  const renderItem = ({ item }) => (
    <View style={styles.crnCard}>
      <View style={styles.crnInfo}>
        <Text style={styles.crnText}>CS 101 (01) [{item}]</Text>
        <Text style={styles.courseName}>Introduction to Computer Science</Text>
      </View>
      <TouchableOpacity
        style={styles.unsubscribeButton}
        onPress={() => unsubscribe(item)}
      >
        <Text style={styles.unsubscribeText}>Unsubscribe</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <LinearGradient
      colors={['#1a1a1a', '#000000']}
      style={styles.gradientContainer}
    >
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />

        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Image source={logo} style={styles.logo} resizeMode="contain" />
            <Text style={styles.title}>ReaperGT</Text>
          </View>
        </View>

        <View style={styles.inputContainer}>
          <TextInput
            value={crnInput}
            onChangeText={setCrnInput}
            placeholder="Enter CRN (e.g. 88321)"
            placeholderTextColor="#666"
            keyboardType="number-pad"
            style={styles.input}
          />
          <TouchableOpacity 
            style={styles.subscribeButton} 
            onPress={subscribe}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={['#CBA135', '#D4B44A']}
              style={styles.subscribeGradient}
            >
              <Text style={styles.subscribeText}>Subscribe</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        <FlatList
          data={trackedCrns}
          keyExtractor={item => item}
          renderItem={renderItem}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>You're not tracking any CRNs yet</Text>
              <Text style={styles.emptySubText}>Add a CRN to start tracking</Text>
            </View>
          }
          contentContainerStyle={
            trackedCrns.length === 0 ? styles.emptyList : styles.listContainer
          }
          showsVerticalScrollIndicator={false}
        />
      </SafeAreaView>
    </LinearGradient>
  );
}

const GOLD = '#CBA135';
const OFFWHITE = '#ECECEC';
const BACKGROUND = '#000000';

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 40 : 56,
    paddingBottom: 24,
  },
  header: {
    marginBottom: 36,
    paddingHorizontal: 4,
    alignItems: 'center',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 52,
    height: 52,
    marginRight: 16,
  },
  title: {
    color: OFFWHITE,
    fontSize: 34,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  inputContainer: {
    flexDirection: 'row',
    marginBottom: 28,
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  input: {
    flex: 1,
    height: 56,
    borderColor: '#333',
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 20,
    color: OFFWHITE,
    marginRight: 16,
    backgroundColor: '#111',
    fontSize: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4.84,
      },
      android: {
        elevation: 6,
      },
    }),
  },
  subscribeButton: {
    height: 56,
    width: 130,
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: GOLD,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.4,
        shadowRadius: 4.84,
      },
      android: {
        elevation: 6,
      },
    }),
  },
  subscribeGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  subscribeText: {
    color: '#000',
    fontWeight: '700',
    fontSize: 17,
    letterSpacing: 0.5,
  },
  listContainer: {
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  crnCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#222',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4.84,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  crnInfo: {
    flex: 1,
    marginRight: 16,
  },
  crnText: {
    color: OFFWHITE,
    fontSize: 19,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  courseName: {
    color: '#888',
    fontSize: 15,
    fontWeight: '500',
  },
  unsubscribeButton: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    backgroundColor: 'rgba(203, 161, 53, 0.15)',
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: GOLD,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 2.84,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  unsubscribeText: {
    color: GOLD,
    fontWeight: '600',
    fontSize: 15,
    letterSpacing: 0.3,
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 80,
    paddingHorizontal: 20,
  },
  emptyText: {
    color: '#666',
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptySubText: {
    color: '#444',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
  },
});
