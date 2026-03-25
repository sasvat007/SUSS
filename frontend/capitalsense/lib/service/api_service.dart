import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = "http://localhost:8000/api/v1";
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // ── Token Storage ──────────────────────────────────────────────────────────

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
  }

  Future<String?> getAccessToken() async => await _storage.read(key: 'access_token');
  Future<String?> getRefreshToken() async => await _storage.read(key: 'refresh_token');

  Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  // ── Auth Methods ───────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/login"),
      headers: {"Content-Type": "application/json", "accept": "application/json"},
      body: jsonEncode({"email": email, "password": password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveTokens(data['access_token'], data['refresh_token']);
      return data;
    } else {
      _handleError(response, "Login failed");
      return {}; 
    }
  }

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
      Uri.parse("$baseUrl/auth/signup"),
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
      _handleError(response, "Signup failed");
      return {}; 
    }
  }

  Future<Map<String, dynamic>> refresh() async {
    final refreshToken = await getRefreshToken();
    if (refreshToken == null) throw Exception('No refresh token found');

    final response = await http.post(
      Uri.parse("$baseUrl/auth/refresh"),
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

  Future<void> logout() async {
    final accessToken = await getAccessToken();
    final refreshToken = await getRefreshToken();
    if (accessToken == null || refreshToken == null) return;

    await http.post(
      Uri.parse("$baseUrl/auth/logout"),
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": "Bearer $accessToken"
      },
      body: jsonEncode({"refresh_token": refreshToken}),
    );
    await clearTokens();
  }

  // ── Questionnaire Methods ──────────────────────────────────────────────────

  Future<Map<String, dynamic>> checkQuestionnaireDue() async {
    final accessToken = await getAccessToken();
    final response = await http.get(
      Uri.parse("$baseUrl/questionnaire/due"),
      headers: {
        "accept": "application/json",
        "Authorization": "Bearer $accessToken"
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to check questionnaire status");
      return {}; 
    }
  }

  Future<Map<String, dynamic>> submitQuestionnaire({
    required double minSafetyBuffer,
    required bool partialPaymentsAllowed,
    required int paymentDelayTolerance,
    required List<String> nonNegotiableObligations,
  }) async {
    final accessToken = await getAccessToken();
    final response = await http.post(
      Uri.parse("$baseUrl/questionnaire/submit"),
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": "Bearer $accessToken"
      },
      body: jsonEncode({
        "min_safety_buffer": minSafetyBuffer,
        "partial_payments_allowed": partialPaymentsAllowed,
        "payment_delay_tolerance": paymentDelayTolerance,
        "non_negotiable_obligations": nonNegotiableObligations,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Submission failed");
      return {}; 
    }
  }

  // ── Utils ──────────────────────────────────────────────────────────────────

  void _handleError(http.Response response, String defaultMsg) {
    try {
      final decoded = jsonDecode(response.body);
      String errorMessage = defaultMsg;
      if (decoded['detail'] is List) {
        errorMessage = decoded['detail'][0]['msg'] ?? defaultMsg;
      } else if (decoded['detail'] is String) {
        errorMessage = decoded['detail'];
      }
      throw Exception(errorMessage);
    } catch (e) {
      throw Exception(defaultMsg);
    }
  }
}