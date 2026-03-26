import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String _configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );
  static String get baseUrl {
    if (_configuredBaseUrl.isNotEmpty) {
      return _configuredBaseUrl;
    }
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return "http://10.0.2.2:8000/api/v1";
    }
    return "http://localhost:8000/api/v1";
  }

  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  // ── Token Storage ──────────────────────────────────────────────────────────

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: 'access_token', value: accessToken);
    await _storage.write(key: 'refresh_token', value: refreshToken);
  }

  Future<String?> getAccessToken() async =>
      await _storage.read(key: 'access_token');
  Future<String?> getRefreshToken() async =>
      await _storage.read(key: 'refresh_token');

  Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  Future<Map<String, String>> _authHeaders() async {
    final token = await getAccessToken();
    return {
      "Content-Type": "application/json",
      "accept": "application/json",
      "Authorization": "Bearer $token",
    };
  }

  // ── Auth Methods ───────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/login"),
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
        "accept": "application/json",
      },
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
        "Authorization": "Bearer $accessToken",
      },
      body: jsonEncode({"refresh_token": refreshToken}),
    );
    await clearTokens();
  }

  Future<Map<String, dynamic>> getProfile() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/auth/me"),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to load profile");
      return {};
    }
  }

  // ── Dashboard (Engine Analysis) ───────────────────────────────────────────

  Future<Map<String, dynamic>> getDashboardSummary() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/dashboard/summary"),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to load dashboard");
      return {};
    }
  }

  // ── Obligations ───────────────────────────────────────────────────────────

  Future<List<dynamic>> getObligations() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/obligations"),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to load obligations");
      return [];
    }
  }

  Future<Map<String, dynamic>> createObligation({
    required String description,
    required double amount,
    required String dueDate,
    String? vendorId,
    String? vendorName,
  }) async {
    final headers = await _authHeaders();
    final body = {
      "description": description,
      "amount": amount,
      "due_date": dueDate,
    };
    if (vendorId != null) body["vendor_id"] = vendorId;
    if (vendorName != null) body["vendor_name"] = vendorName;
    final response = await http.post(
      Uri.parse("$baseUrl/obligations"),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to create obligation");
      return {};
    }
  }

  Future<Map<String, dynamic>> markObligationPaid(
    String obId,
    double amount, {
    bool isFull = true,
  }) async {
    final headers = await _authHeaders();
    final body = {
      "payment_type": isFull ? "full" : "partial",
      "amount": amount,
    };
    final response = await http.patch(
      Uri.parse("$baseUrl/obligations/$obId/mark-paid"),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to mark obligation as paid");
      return {};
    }
  }

  // ── Receivables ───────────────────────────────────────────────────────────

  Future<List<dynamic>> getReceivables() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/receivables"),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to load receivables");
      return [];
    }
  }

  Future<Map<String, dynamic>> createReceivable({
    required String clientName,
    required double amount,
    required String dueDate,
    String? description,
  }) async {
    final headers = await _authHeaders();
    final response = await http.post(
      Uri.parse("$baseUrl/receivables"),
      headers: headers,
      body: jsonEncode({
        "client_name": clientName,
        "amount": amount,
        "due_date": dueDate,
        "description": description,
      }),
    );
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to create receivable");
      return {};
    }
  }

  Future<Map<String, dynamic>> markReceivableReceived(
    String recId,
    double amount, {
    bool isFull = true,
  }) async {
    final headers = await _authHeaders();
    final body = {
      "payment_type": isFull ? "full" : "partial",
      "amount": amount,
    };
    final response = await http.patch(
      Uri.parse("$baseUrl/receivables/$recId/mark-received"),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to mark receivable as received");
      return {};
    }
  }

  // ── Funds ─────────────────────────────────────────────────────────────────

  Future<List<dynamic>> getFunds() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/funds"),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to load funds");
      return [];
    }
  }

  Future<Map<String, dynamic>> createFund({
    required String sourceName,
    required double amount,
    required String dateReceived,
    String? notes,
  }) async {
    final headers = await _authHeaders();
    final response = await http.post(
      Uri.parse("$baseUrl/funds"),
      headers: headers,
      body: jsonEncode({
        "source_name": sourceName,
        "amount": amount,
        "date_received": dateReceived,
        "notes": notes,
      }),
    );
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to add fund");
      return {};
    }
  }

  // ── Scenario Simulation ───────────────────────────────────────────────────

  Future<Map<String, dynamic>> simulateScenario({
    double? balance,
    String riskLevel = "MODERATE",
    double? minCashBuffer,
    int? timeHorizonDays,
  }) async {
    final headers = await _authHeaders();
    final scenario = <String, dynamic>{"risk_level": riskLevel};
    if (balance != null) scenario["balance"] = balance;
    if (minCashBuffer != null) scenario["min_cash_buffer"] = minCashBuffer;
    if (timeHorizonDays != null)
      scenario["time_horizon_days"] = timeHorizonDays;

    final response = await http.post(
      Uri.parse("$baseUrl/scenario/simulate"),
      headers: headers,
      body: jsonEncode({"scenario": scenario}),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Simulation failed");
      return {};
    }
  }

  // ── Questionnaire Methods ──────────────────────────────────────────────────

  Future<Map<String, dynamic>> checkQuestionnaireDue() async {
    final headers = await _authHeaders();
    final response = await http.get(
      Uri.parse("$baseUrl/questionnaire/due"),
      headers: headers,
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
    final headers = await _authHeaders();
    final response = await http.post(
      Uri.parse("$baseUrl/questionnaire/submit"),
      headers: headers,
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

  // ── OCR ───────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> uploadOcr(String filePath) async {
    final token = await getAccessToken();
    final request = http.MultipartRequest(
      'POST',
      Uri.parse("$baseUrl/ocr/upload"),
    );
    request.headers.addAll({"Authorization": "Bearer $token"});
    request.files.add(await http.MultipartFile.fromPath('file', filePath));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "OCR extraction failed");
      return {};
    }
  }

  // ── Utils ──────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> createPaymentLink(
    String obligationId,
    double amount,
  ) async {
    final headers = await _authHeaders();
    final body = {"obligation_id": obligationId, "amount": amount};
    final response = await http.post(
      Uri.parse("$baseUrl/payments/create"),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to create payment link");
      return {};
    }
  }

  Future<Map<String, dynamic>> deferObligation(
    String obligationId, {
    int days = 30,
  }) async {
    final headers = await _authHeaders();
    final response = await http.patch(
      Uri.parse("$baseUrl/obligations/$obligationId/defer?days=$days"),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _handleError(response, "Failed to defer obligation");
      return {};
    }
  }

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
      if (e is Exception) rethrow;
      throw Exception(defaultMsg);
    }
  }
}
