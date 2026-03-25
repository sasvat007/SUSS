import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = "http://localhost:8000/api/v1/auth";
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // Save tokens securely
  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
  }

  // Get tokens
  Future<String?> getAccessToken() async => await _storage.read(key: 'access_token');
  Future<String?> getRefreshToken() async => await _storage.read(key: 'refresh_token');

  // Clear tokens
  Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/login"),
      headers: {"Content-Type": "application/json", "accept": "application/json"},
      body: jsonEncode({"email": email, "password": password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveTokens(data['access_token'], data['refresh_token']);
      return data;
    } else {
      final decoded = jsonDecode(response.body);
      String errorMessage = "Login failed";
      if (decoded['detail'] is List) {
        errorMessage = decoded['detail'][0]['msg'] ?? errorMessage;
      } else if (decoded['detail'] is String) {
        errorMessage = decoded['detail'];
      }
      throw Exception(errorMessage);
    }
  }

  // Signup
  Future<Map<String, dynamic>> signup({
    required String fullName,
    required String email,
    required String phoneNumber,
    required String businessName,
    required String gstNumber,
    required String password,
    String? officeAddress,
  }) async {
    final response = await http.post(
      Uri.parse("$baseUrl/signup"),
      headers: {"Content-Type": "application/json", "accept": "application/json"},
      body: jsonEncode({
        "full_name": fullName,
        "email": email,
        "phone_number": phoneNumber,
        "business_name": businessName,
        "gst_number": gstNumber,
        "password": password,
        "office_address": officeAddress,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      await saveTokens(data['access_token'], data['refresh_token']);
      return data;
    } else {
      final decoded = jsonDecode(response.body);
      String errorMessage = "Signup failed";
      if (decoded['detail'] is List) {
        errorMessage = decoded['detail'][0]['msg'] ?? errorMessage;
      } else if (decoded['detail'] is String) {
        errorMessage = decoded['detail'];
      }
      throw Exception(errorMessage);
    }
  }

  // Refresh Token
  Future<Map<String, dynamic>> refresh() async {
    final refreshToken = await getRefreshToken();
    if (refreshToken == null) throw Exception('No refresh token found');

    final response = await http.post(
      Uri.parse("$baseUrl/refresh"),
      headers: {"Content-Type": "application/json", "accept": "application/json"},
      body: jsonEncode({"refresh_token": refreshToken}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveTokens(data['access_token'], data['refresh_token']);
      return data;
    } else {
      await clearTokens();
      throw Exception('Session expired');
    }
  }

  // Logout
  Future<void> logout() async {
    final accessToken = await getAccessToken();
    final refreshToken = await getRefreshToken();
    
    if (accessToken == null || refreshToken == null) return;

    final response = await http.post(
      Uri.parse("$baseUrl/logout"),
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": "Bearer $accessToken"
      },
      body: jsonEncode({"refresh_token": refreshToken}),
    );

    await clearTokens();
    if (response.statusCode != 204) {
      // Log error but we clear tokens anyway
    }
  }
}