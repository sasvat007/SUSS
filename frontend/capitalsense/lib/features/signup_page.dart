import 'package:flutter/material.dart';
import 'package:capitalsense/service/api_service.dart';
import 'package:capitalsense/widgets/animated_background.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final ApiService apiService = ApiService();
  bool _obscurePassword = true;
  bool _isLoading = false;

  final fullNameController = TextEditingController();
  final emailController = TextEditingController();
  final phoneController = TextEditingController();
  final businessNameController = TextEditingController();
  final gstController = TextEditingController();
  final addressController = TextEditingController();
  final passwordController = TextEditingController();

  Future<void> signup() async {
    // Basic validation
    if (fullNameController.text.isEmpty ||
        emailController.text.isEmpty ||
        phoneController.text.isEmpty ||
        businessNameController.text.isEmpty ||
        gstController.text.isEmpty ||
        passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please fill all required fields'),
          backgroundColor: Colors.red,
          duration: Duration(milliseconds: 1500),
        ),
      );
      return;
    }

    if (gstController.text.length != 15) {
       ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('GST Number must be exactly 15 characters'),
          backgroundColor: Colors.red,
          duration: Duration(milliseconds: 1500),
        ),
      );
      return;
    }

    // Instead of calling signup API here, we pass the data to the questionnaire
    if (mounted) {
      Navigator.pushNamed(
        context, 
        '/questionnaire',
        arguments: {
          'fullName': fullNameController.text.trim(),
          'email': emailController.text.trim(),
          'phoneNumber': phoneController.text.trim(),
          'businessName': businessNameController.text.trim(),
          'gstNumber': gstController.text.trim().toUpperCase(),
          'password': passwordController.text,
          'officeAddress': addressController.text.trim().isEmpty ? null : addressController.text.trim(),
        }
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(vertical: 30),
              child: Column(
                children: [
                  /// Logo
                  Container(
                    height: 60,
                    width: 60,
                    decoration: BoxDecoration(
                      color: Colors.green.shade800,
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: const Icon(Icons.business, color: Colors.white, size: 30),
                  ),

                  const SizedBox(height: 15),

                  const Text(
                    "CREATE ACCOUNT",
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      letterSpacing: 1.2,
                    ),
                  ),

                  const Text(
                    "Secure Financial Onboarding",
                    style: TextStyle(color: Colors.white70, fontSize: 14),
                  ),

                  const SizedBox(height: 25),

                  /// Signup Card
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 25),
                    padding: const EdgeInsets.all(25),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.95),
                      borderRadius: BorderRadius.circular(25),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabel("FULL NAME"),
                        _buildTextField(fullNameController, "John Doe", Icons.person),
                        
                        const SizedBox(height: 15),
                        _buildLabel("BUSINESS EMAIL"),
                        _buildTextField(emailController, "corp@gst.in", Icons.email, keyboardType: TextInputType.emailAddress),

                        const SizedBox(height: 15),
                        _buildLabel("PHONE NUMBER"),
                        _buildTextField(phoneController, "+91 98765 43210", Icons.phone, keyboardType: TextInputType.phone),

                        const SizedBox(height: 15),
                        _buildLabel("BUSINESS NAME"),
                        _buildTextField(businessNameController, "Reliance Ind.", Icons.apartment),

                        const SizedBox(height: 15),
                        _buildLabel("GST NUMBER"),
                        _buildTextField(gstController, "22AAAAA0000A1Z5", Icons.assured_workload, textCapitalization: TextCapitalization.characters),

                        const SizedBox(height: 15),
                        _buildLabel("OFFICE ADDRESS (OPTIONAL)"),
                        _buildTextField(addressController, "Mumbai, India", Icons.location_on, maxLines: 2),

                        const SizedBox(height: 15),
                        _buildLabel("PASSWORD"),
                        _buildPasswordField(),

                        const SizedBox(height: 25),

                        /// Signup Button
                        SizedBox(
                          width: double.infinity,
                          height: 55,
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF0F5B44),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                            ),
                            onPressed: _isLoading ? null : signup,
                            child: _isLoading
                                ? const CircularProgressIndicator(color: Colors.white)
                                : const Text(
                                    "Finish Registration",
                                    style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                                  ),
                          ),
                        ),

                        const SizedBox(height: 25),

                        /// Back to Login
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text("Already registered? ", style: TextStyle(color: Colors.black87)),
                            GestureDetector(
                              onTap: () => Navigator.pop(context),
                              child: const Text(
                                "Login",
                                style: TextStyle(color: Color(0xFF0F5B44), fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Text(text, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String hint,
    IconData icon, {
    TextInputType keyboardType = TextInputType.text,
    TextCapitalization textCapitalization = TextCapitalization.none,
    int maxLines = 1,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      textCapitalization: textCapitalization,
      maxLines: maxLines,
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon),
        filled: true,
        fillColor: Colors.grey.shade200,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.all(15),
      ),
    );
  }

  Widget _buildPasswordField() {
    return TextField(
      controller: passwordController,
      obscureText: _obscurePassword,
      decoration: InputDecoration(
        prefixIcon: const Icon(Icons.lock),
        suffixIcon: IconButton(
          icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
        ),
        filled: true,
        fillColor: Colors.grey.shade200,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.all(15),
      ),
    );
  }
}
