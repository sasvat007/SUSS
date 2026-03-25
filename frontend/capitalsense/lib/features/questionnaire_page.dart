import 'package:flutter/material.dart';
import 'package:capitalsense/service/api_service.dart';
import 'package:capitalsense/widgets/animated_background.dart';

class QuestionnaireScreen extends StatefulWidget {
  const QuestionnaireScreen({super.key});

  @override
  State<QuestionnaireScreen> createState() => _QuestionnaireScreenState();
}

class _QuestionnaireScreenState extends State<QuestionnaireScreen> {
  final ApiService _apiService = ApiService();
  final PageController _pageController = PageController();
  int _currentPage = 0;
  bool _isLoading = false;

  // Form Controllers
  final TextEditingController _bufferController = TextEditingController(text: "50000");

  // Form State
  double _minSafetyBuffer = 50000;
  bool _partialPaymentsAllowed = true;
  int _paymentDelayTolerance = 7;
  List<String> _nonNegotiableObligations = [];

  final List<String> _obligationOptions = [
    "Rent",
    "Salaries",
    "Government/GST",
    "Utilities",
    "Loan EMIs",
    "Suppliers"
  ];

  Future<void> _submit() async {
    final Map<String, dynamic>? regData = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>?;

    setState(() => _isLoading = true);
    try {
      if (regData != null) {
        // Step A: Create User
        await _apiService.signup(
          fullName: regData['fullName'],
          email: regData['email'],
          phoneNumber: regData['phoneNumber'],
          businessName: regData['businessName'],
          gstNumber: regData['gstNumber'],
          password: regData['password'],
          officeAddress: regData['officeAddress'],
        );
      }

      // Step B: Submit questionnaire using the tokens now in storage
      await _apiService.submitQuestionnaire(
        minSafetyBuffer: _minSafetyBuffer,
        partialPaymentsAllowed: _partialPaymentsAllowed,
        paymentDelayTolerance: _paymentDelayTolerance,
        nonNegotiableObligations: _nonNegotiableObligations,
      );

      if (mounted) {
        Navigator.pushReplacementNamed(context, '/dashboard');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceAll('Exception: ', '')),
            backgroundColor: Colors.red,
            duration: const Duration(milliseconds: 1500),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _nextPage() {
    if (_currentPage < 3) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _submit();
    }
  }

  void _prevPage() {
    if (_currentPage > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedGradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          elevation: 0,
          backgroundColor: Colors.transparent,
          leading: _currentPage > 0
              ? IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: _prevPage,
                )
              : null,
          title: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: (_currentPage + 1) / 4,
              backgroundColor: Colors.white24,
              color: Colors.white,
              minHeight: 8,
            ),
          ),
        ),
        body: Container(
          margin: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.92),
            borderRadius: BorderRadius.circular(30),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                spreadRadius: 5,
              ),
            ],
          ),
          child: _isLoading
              ? const Center(child: CircularProgressIndicator(color: Color(0xFF0F5B44)))
              : PageView(
                  controller: _pageController,
                  onPageChanged: (idx) => setState(() => _currentPage = idx),
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _buildBufferStep(),
                    _buildToleranceStep(),
                    _buildObligationsStep(),
                    _buildSummaryStep(),
                  ],
                ),
        ),
        bottomNavigationBar: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 25),
            child: SizedBox(
              height: 55,
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0F5B44),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  elevation: 5,
                ),
                onPressed: _nextPage,
                child: Text(
                  _currentPage == 3 ? "Complete Onboarding" : "Next Question",
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepContainer({required String title, required String subtitle, required Widget child}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
          const SizedBox(height: 10),
          Text(subtitle, style: const TextStyle(fontSize: 14, color: Colors.black54)),
          const SizedBox(height: 35),
          Expanded(child: child),
        ],
      ),
    );
  }

  Widget _buildBufferStep() {
    return _buildStepContainer(
      title: "Cash Safety Buffer",
      subtitle: "What is the minimum cash balance you want to maintain in your account at all times?",
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFF0F5B44).withOpacity(0.2)),
            ),
            child: Row(
              children: [
                const Text("₹", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0F5B44))),
                const SizedBox(width: 15),
                Expanded(
                  child: TextField(
                    controller: _bufferController,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF0F5B44)),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      hintText: "Enter amount",
                    ),
                    onChanged: (val) {
                      setState(() {
                        _minSafetyBuffer = double.tryParse(val) ?? 0;
                      });
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          const Text("Enter your minimum cash reserve requirement", style: TextStyle(color: Colors.grey, fontSize: 12)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(15),
            ),
            child: SwitchListTile(
              title: const Text("Partial Payments", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              subtitle: const Text("Allow installments?", style: TextStyle(fontSize: 12)),
              value: _partialPaymentsAllowed,
              activeColor: const Color(0xFF0F5B44),
              onChanged: (val) => setState(() => _partialPaymentsAllowed = val),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildToleranceStep() {
    return _buildStepContainer(
      title: "Delay Tolerance",
      subtitle: "How many days can you comfortably delay a non-critical payment?",
      child: ListView(
        children: [
          _buildDayOption(0, "Immediate Only", "Zero tolerance for delays"),
          _buildDayOption(3, "3 Days", "Short term flexibility"),
          _buildDayOption(7, "7 Days", "One week window"),
          _buildDayOption(15, "15 Days", "Extended tolerance"),
          _buildDayOption(30, "30 Days", "High flexibility"),
        ],
      ),
    );
  }

  Widget _buildDayOption(int days, String title, String sub) {
    bool isSelected = _paymentDelayTolerance == days;
    return GestureDetector(
      onTap: () => setState(() => _paymentDelayTolerance = days),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0F5B44).withOpacity(0.08) : Colors.white,
          border: Border.all(color: isSelected ? const Color(0xFF0F5B44) : Colors.grey.shade200, width: 2),
          borderRadius: BorderRadius.circular(15),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today, color: isSelected ? const Color(0xFF0F5B44) : Colors.grey),
            const SizedBox(width: 20),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: isSelected ? const Color(0xFF0F5B44) : Colors.black)),
                  Text(sub, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
            ),
            if (isSelected) const Icon(Icons.check_circle, color: Color(0xFF0F5B44)),
          ],
        ),
      ),
    );
  }

  Widget _buildObligationsStep() {
    return _buildStepContainer(
      title: "Crucial Obligations",
      subtitle: "Which of these payments are COMPLETELY non-negotiable? Select all that apply.",
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: _obligationOptions.map((opt) {
          bool isSelected = _nonNegotiableObligations.contains(opt);
          return FilterChip(
            label: Text(opt),
            selected: isSelected,
            onSelected: (val) {
              setState(() {
                if (val) {
                  _nonNegotiableObligations.add(opt);
                } else {
                  _nonNegotiableObligations.remove(opt);
                }
              });
            },
            selectedColor: const Color(0xFF0F5B44).withOpacity(0.15),
            checkmarkColor: const Color(0xFF0F5B44),
            labelStyle: TextStyle(
              color: isSelected ? const Color(0xFF0F5B44) : Colors.black87,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildSummaryStep() {
    return _buildStepContainer(
      title: "Review Details",
      subtitle: "Almost done! Here is a summary of your risk profile settings.",
      child: ListView(
        children: [
          _summaryRow("Cash Buffer", "₹ ${_minSafetyBuffer.toInt()}"),
          _summaryRow("Partial Payments", _partialPaymentsAllowed ? "Allowed" : "Not Allowed"),
          _summaryRow("Delay Tolerance", "$_paymentDelayTolerance Days"),
          _summaryRow("Crucial Payments", _nonNegotiableObligations.isEmpty ? "None" : _nonNegotiableObligations.join(", ")),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 15),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.black54)),
          Expanded(
            child: Text(
              value, 
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0F5B44))
            ),
          ),
        ],
      ),
    );
  }
}
