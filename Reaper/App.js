import AsyncStorage from '@react-native-async-storage/async-storage';
import { Picker } from '@react-native-picker/picker';
import React, { useEffect, useState } from 'react';
import {
  Button,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import logo from './assets/transparent_logo.png';

export default function App() {
  const [searchType, setSearchType] = useState('name');
  const [searchQuery, setSearchQuery] = useState('');
  const [courseList, setCourseList] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [enteredPassword, setEnteredPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const storedCourses = await AsyncStorage.getItem('courses');
        if (storedCourses) {
          setCourseList(JSON.parse(storedCourses));
        }
      } catch (e) {
        console.error('Failed to load courses', e);
      }
    };
    loadCourses();
  }, []);

  useEffect(() => {
    const saveCourses = async () => {
      try {
        await AsyncStorage.setItem('courses', JSON.stringify(courseList));
      } catch (e) {
        console.error('Failed to save courses', e);
      }
    };
    saveCourses();
  }, [courseList]);

  const handleSearch = () => {
    if (searchQuery.trim() !== '') {
      const course = {
        number: searchType === 'number' ? searchQuery.trim() : 'CSE101',
        name: searchType === 'name' ? searchQuery.trim() : 'Intro to Programming',
        professor: 'Mr. John Smith',
        credits: 4,
        time: '10 AM - 12 PM',
        days: 'MWF',
      };
      setCourseList([course, ...courseList]);
      setSearchQuery('');
    }
  };

  const handleDelete = (index) => {
    const updatedList = courseList.filter((_, i) => i !== index);
    setCourseList(updatedList);
  };

  //  DEBUG LOGIN SCREEN
  if (debugMode && !isAuthenticated) {
    return (
      <View style={styles.debugContainer}>
        <Text style={styles.debugTitle}>Enter Debug Password</Text>
        <TextInput
          style={styles.debugInput}
          placeholder="Enter password"
          secureTextEntry
          value={enteredPassword}
          onChangeText={setEnteredPassword}
          placeholderTextColor="#ccc"
        />
        <Button
          title="Submit"
          onPress={() => {
            if (enteredPassword === 'letmein123') {
              setIsAuthenticated(true);
            } else {
              alert('Incorrect password');
            }
          }}
        />
        <Button
          title="Back to App"
          onPress={() => {
            setDebugMode(false);
            setEnteredPassword('');
          }}
        />
      </View>
    );
  }

  // DEBUG TOOLS SCREEN
  if (debugMode && isAuthenticated) {
    return (
      <View style={styles.debugContainer}>
        <Text style={styles.debugTitle}>Debug Panel</Text>
        <Button
          title="Log Courses to Console"
          onPress={async () => {
            const data = await AsyncStorage.getItem('courses');
            console.log(JSON.parse(data));
          }}
        />
        <Button
          title="Clear All Courses"
          onPress={async () => {
            await AsyncStorage.removeItem('courses');
            setCourseList([]);
            alert('All courses cleared.');
          }}
          color="#802020"
        />
        <Button
          title="Exit Debug Mode"
          onPress={() => {
            setDebugMode(false);
            setEnteredPassword('');
            setIsAuthenticated(false);
          }}
        />
      </View>
    );
  }

  //  MAIN UI
  return (
    <View style={styles.container}>
      <Image source={logo} style={styles.logo} resizeMode="contain" />

      <View style={styles.searchRow}>
        <View style={styles.pickerWrapper}>
          <Picker
            selectedValue={searchType}
            style={styles.picker}
            onValueChange={(itemValue) => setSearchType(itemValue)}
            mode="dropdown"
          >
            <Picker.Item label="Course Name" value="name" />
            <Picker.Item label="Course Number" value="number" />
          </Picker>
        </View>
        <TextInput
          style={styles.searchBar}
          placeholder={`Search by ${searchType}`}
          placeholderTextColor="#ccc"
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearch}
        />
      </View>

      <View style={styles.buttonContainer}>
        <Button
          title={editMode ? 'Exit Edit Mode' : 'Enter Edit Mode'}
          color="#b38e51"
          onPress={() => setEditMode(!editMode)}
        />
      </View>

      <ScrollView horizontal style={styles.scrollContainer}>
        <View>
          <View style={styles.tableHeader}>
            <Text style={[styles.headerCell, { width: 100 }]}>Number</Text>
            <Text style={[styles.headerCell, { width: 150 }]}>Name</Text>
            <Text style={[styles.headerCell, { width: 130 }]}>Professor</Text>
            <Text style={[styles.headerCell, { width: 80 }]}>Credits</Text>
            <Text style={[styles.headerCell, { width: 140 }]}>Time</Text>
            <Text style={[styles.headerCell, { width: 80 }]}>Days</Text>
          </View>
          {courseList.map((course, index) => (
            <TouchableOpacity
              key={index}
              onPress={() => editMode && handleDelete(index)}
              style={[
                styles.tableRow,
                editMode && { backgroundColor: '#802020' },
              ]}
            >
              <Text style={[styles.cell, { width: 100 }]}>{course.number}</Text>
              <Text style={[styles.cell, { width: 150 }]}>{course.name}</Text>
              <Text style={[styles.cell, { width: 130 }]}>{course.professor}</Text>
              <Text style={[styles.cell, { width: 80 }]}>{course.credits}</Text>
              <Text style={[styles.cell, { width: 140 }]}>{course.time}</Text>
              <Text style={[styles.cell, { width: 80 }]}>{course.days}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <View style={styles.buttonContainer}>
        <Button
          title="Enter Debug Mode"
          color="#b38e51"
          onPress={() => setDebugMode(true)}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 200,
    alignItems: 'center',
    backgroundColor: '#696969',
  },
  logo: {
    width: 200,
    height: 100,
    marginBottom: 20,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '90%',
    marginBottom: 10,
  },
  pickerWrapper: {
    width: '40%',
    borderWidth: 1,
    borderColor: '#b38e51',
    borderRadius: 8,
    marginRight: 10,
    backgroundColor: '#4a4949',
  },
  picker: {
    height: 40,
    color: '#f0e9d4',
  },
  searchBar: {
    flex: 1,
    height: 40,
    borderColor: '#b38e51',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    backgroundColor: '#4a4949',
    color: '#f0e9d4',
  },
  buttonContainer: {
    marginVertical: 10,
  },
  scrollContainer: {
    width: '100%',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#4a4949',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderColor: '#b38e51',
  },
  headerCell: {
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 14,
    paddingHorizontal: 5,
    color: '#b38e51',
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderColor: '#888',
  },
  cell: {
    textAlign: 'center',
    fontSize: 14,
    color: '#f0e9d4',
    paddingHorizontal: 5,
  },
  debugContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#5c5b5b',
    padding: 20,
  },
  debugTitle: {
    fontSize: 24,
    marginBottom: 20,
    color: '#f0e9d4',
  },
  debugInput: {
    width: '80%',
    height: 40,
    borderColor: '#b38e51',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    marginBottom: 20,
    color: '#f0e9d4',
    backgroundColor: '#4a4949',
  },
});
