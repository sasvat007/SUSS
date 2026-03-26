import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:capitalsense/features/admin_page.dart';
import 'package:capitalsense/features/strategy_tab.dart';
import 'package:capitalsense/widgets/animated_background.dart';
import 'package:capitalsense/service/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedTab = 0;
  final ApiService _api = ApiService();

  bool _isLoading = true;
  Map<String, dynamic>? _dashboardData;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final data = await _api.getDashboardSummary();
      if (mounted) {
        setState(() {
          _dashboardData = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  Widget _buildCurrentTab() {
    switch (_selectedTab) {
      case 0:
        return _buildOverviewTab();
      case 1:
        return StrategyTab(
          dashboardData: _dashboardData,
          onRefresh: _loadDashboard,
        );
      case 2:
        return _buildRecordsTab();
      case 3:
        return const AdminProfileScreen();
      default:
        return _buildOverviewTab();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AnimatedGradientBackground(
        child: _buildCurrentTab(),
      ),
      bottomNavigationBar: _buildBottomNav(),
      floatingActionButton: _selectedTab == 0
          ? FloatingActionButton(
              backgroundColor: const Color(0xFF0F5B44),
              onPressed: () => _showQuickActionsMenu(context),
              child: const Icon(Icons.add, color: Colors.white, size: 30),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }

  // ── Quick Actions ──────────────────────────────────────────────────────────

  void _showQuickActionsMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(topLeft: Radius.circular(30), topRight: Radius.circular(30)),
      ),
      builder: (sheetCtx) {
        bool isReceivable = true; // local toggle state
        return StatefulBuilder(
          builder: (context, setSheetState) => Container(
            padding: const EdgeInsets.fromLTRB(25, 20, 25, 30),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2))),
                const SizedBox(height: 22),
                const Text("Quick Financial Actions", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
                const SizedBox(height: 18),

                // ── Receivable / Payable Toggle ─────────────────────────────
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(18)),
                  child: Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setSheetState(() => isReceivable = true),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: isReceivable ? Colors.blue.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: isReceivable ? [BoxShadow(color: Colors.blue.shade700.withOpacity(0.3), blurRadius: 6, offset: const Offset(0, 2))] : [],
                            ),
                            child: Center(
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.arrow_downward, size: 14, color: isReceivable ? Colors.white : Colors.black38),
                                  const SizedBox(width: 6),
                                  Text("RECEIVABLE", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: isReceivable ? Colors.white : Colors.black38)),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setSheetState(() => isReceivable = false),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            decoration: BoxDecoration(
                              color: !isReceivable ? Colors.red.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: !isReceivable ? [BoxShadow(color: Colors.red.shade700.withOpacity(0.3), blurRadius: 6, offset: const Offset(0, 2))] : [],
                            ),
                            child: Center(
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.arrow_upward, size: 14, color: !isReceivable ? Colors.white : Colors.black38),
                                  const SizedBox(width: 6),
                                  Text("PAYABLE", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: !isReceivable ? Colors.white : Colors.black38)),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: Text(
                    isReceivable ? "Money coming IN to you (clients owe you)" : "Money going OUT from you (you owe others)",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 11,
                      color: isReceivable ? Colors.blue.shade700 : Colors.red.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(height: 10),

                // ── Action Buttons ──────────────────────────────────────────
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildQuickActionItem(sheetCtx, "Upload Invoice", Icons.document_scanner, () => _handleInvoiceFlow(sheetCtx)),
                    _buildQuickActionItem(sheetCtx, "Add Manually", Icons.edit_note, () => _showAddManualEntryDialog(sheetCtx, isReceivable)),
                    _buildQuickActionItem(sheetCtx, "Add Fund", Icons.add_business, () => _showAddFundDialog(sheetCtx)),
                  ],
                ),
                const SizedBox(height: 10),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildQuickActionItem(BuildContext context, String label, IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: () {
        Navigator.pop(context);
        onTap();
      },
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: const Color(0xFF0F5B44).withOpacity(0.08), borderRadius: BorderRadius.circular(20)),
            child: Icon(icon, color: const Color(0xFF0F5B44), size: 28),
          ),
          const SizedBox(height: 10),
          Text(label.split(" ").last, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black54)),
        ],
      ),
    );
  }

  // ── Add Manual Entry Dialog (Unified Receivable/Payable) ────────────────────

  void _showAddManualEntryDialog(BuildContext sheetCtx, bool isReceivable) {
    final nameCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    final dateCtrl = TextEditingController();
    bool entryIsReceivable = isReceivable;
    // Capture the outer page context explicitly before showing dialog
    final pageContext = context;

    showDialog(
      context: pageContext,
      builder: (dialogCtx) => StatefulBuilder(
        builder: (_, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
          title: Center(
            child: Text(
              entryIsReceivable ? "Add Receivable" : "Add Payable",
              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E)),
            ),
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Toggle inside dialog too
                Container(
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(14)),
                  child: Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setDialogState(() => entryIsReceivable = false),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 9),
                            decoration: BoxDecoration(
                              color: !entryIsReceivable ? Colors.red.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(11),
                            ),
                            child: Center(child: Text("PAYABLE", style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: !entryIsReceivable ? Colors.white : Colors.black45))),
                          ),
                        ),
                      ),
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setDialogState(() => entryIsReceivable = true),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 9),
                            decoration: BoxDecoration(
                              color: entryIsReceivable ? Colors.blue.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(11),
                            ),
                            child: Center(child: Text("RECEIVABLE", style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: entryIsReceivable ? Colors.white : Colors.black45))),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _dialogTextField(nameCtrl, entryIsReceivable ? "Client Name" : "Vendor / Payee", Icons.business),
                const SizedBox(height: 12),
                _dialogTextField(descCtrl, "Description", Icons.description),
                const SizedBox(height: 12),
                _dialogTextField(amountCtrl, "Amount (₹)", Icons.currency_rupee, isNumber: true),
                const SizedBox(height: 12),
                _dialogDateField(dateCtrl, entryIsReceivable ? "Expected Date" : "Due Date", dialogCtx),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogCtx), child: const Text("Cancel")),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: entryIsReceivable ? Colors.blue.shade700 : Colors.red.shade700,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () async {
                if (amountCtrl.text.isEmpty || dateCtrl.text.isEmpty) return;
                // Close dialog immediately so no black screen
                Navigator.pop(dialogCtx);
                try {
                  if (entryIsReceivable) {
                    await _api.createReceivable(
                      clientName: nameCtrl.text.isNotEmpty ? nameCtrl.text : "Unknown Client",
                      amount: double.parse(amountCtrl.text),
                      dueDate: dateCtrl.text,
                      description: descCtrl.text.isNotEmpty ? descCtrl.text : null,
                    );
                  } else {
                    await _api.createObligation(
                      description: descCtrl.text.isNotEmpty ? descCtrl.text : "Manual entry",
                      amount: double.parse(amountCtrl.text),
                      dueDate: dateCtrl.text,
                      vendorName: nameCtrl.text.isNotEmpty ? nameCtrl.text : null,
                    );
                  }
                  if (mounted) {
                    ScaffoldMessenger.of(pageContext).showSnackBar(SnackBar(
                      content: Text(entryIsReceivable ? "✓ Receivable added!" : "✓ Payable added!"),
                      backgroundColor: entryIsReceivable ? Colors.blue.shade700 : Colors.red.shade700,
                    ));
                    _loadDashboard(); // refresh dashboard silently
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(pageContext).showSnackBar(
                      SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
                    );
                  }
                }
              },
              child: const Text("Save", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  // ── Add Expense Dialog (kept for legacy, now hidden from quick actions) ──────

  void _showAddExpenseDialog(BuildContext context) {
    final vendorCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    final dateCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
        title: const Center(child: Text("Add Expense", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E)))),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogTextField(vendorCtrl, "Vendor / Payee (opt)", Icons.business),
              const SizedBox(height: 12),
              _dialogTextField(descCtrl, "Description", Icons.description),
              const SizedBox(height: 12),
              _dialogTextField(amountCtrl, "Amount (₹)", Icons.currency_rupee, isNumber: true),
              const SizedBox(height: 12),
              _dialogDateField(dateCtrl, "Due Date", ctx),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0F5B44), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            onPressed: () async {
              if (amountCtrl.text.trim().isEmpty || dateCtrl.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Please fill Amount and Date."), backgroundColor: Colors.red),
                );
                return;
              }
              Navigator.pop(ctx);
              setState(() => _isLoading = true);
              try {
                await _api.createObligation(
                  description: descCtrl.text,
                  amount: double.parse(amountCtrl.text),
                  dueDate: dateCtrl.text,
                  vendorName: vendorCtrl.text.isNotEmpty ? vendorCtrl.text : null,
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Expense added successfully!"), backgroundColor: Color(0xFF0F5B44)),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
                  );
                }
              } finally {
                if (mounted) setState(() => _isLoading = false);
                _loadDashboard();
              }
            },
            child: const Text("Add", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Add Receipt Dialog ─────────────────────────────────────────────────────

  void _showAddReceiptDialog(BuildContext context) {
    final clientCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    final dateCtrl = TextEditingController();
    final descCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
        title: const Center(child: Text("Add Receivable", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E)))),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogTextField(clientCtrl, "Client Name", Icons.person),
              const SizedBox(height: 12),
              _dialogTextField(amountCtrl, "Amount (₹)", Icons.currency_rupee, isNumber: true),
              const SizedBox(height: 12),
              _dialogDateField(dateCtrl, "Expected Date", ctx),
              const SizedBox(height: 12),
              _dialogTextField(descCtrl, "Description (opt)", Icons.note),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0F5B44), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            onPressed: () async {
              if (clientCtrl.text.isEmpty || amountCtrl.text.isEmpty || dateCtrl.text.isEmpty) return;
              Navigator.pop(ctx);
              try {
                await _api.createReceivable(
                  clientName: clientCtrl.text,
                  amount: double.parse(amountCtrl.text),
                  dueDate: dateCtrl.text,
                  description: descCtrl.text.isNotEmpty ? descCtrl.text : null,
                );
                _loadDashboard();
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Receivable added!"), backgroundColor: Color(0xFF0F5B44)),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
                  );
                }
              }
            },
            child: const Text("Add", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Add Fund Dialog ────────────────────────────────────────────────────────

  void _showAddFundDialog(BuildContext sheetCtx) {
    final sourceCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    final dateCtrl = TextEditingController();

    // Use the main page context to ensure the dialog stays visible after sheet is popped
    final pageContext = context;

    showDialog(
      context: pageContext,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
        title: const Center(child: Text("Add Fund", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E)))),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _dialogTextField(sourceCtrl, "Source Name", Icons.account_balance),
              const SizedBox(height: 12),
              _dialogTextField(amountCtrl, "Amount (₹)", Icons.currency_rupee, isNumber: true),
              const SizedBox(height: 12),
              _dialogDateField(dateCtrl, "Date Received", ctx),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0F5B44), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            onPressed: () async {
              if (sourceCtrl.text.trim().isEmpty || amountCtrl.text.trim().isEmpty || dateCtrl.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Please fill all fields."), backgroundColor: Colors.red),
                );
                return;
              }
              final messenger = ScaffoldMessenger.of(context);
              Navigator.pop(ctx);
              try {
                await _api.createFund(
                  sourceName: sourceCtrl.text,
                  amount: double.tryParse(amountCtrl.text) ?? 0,
                  dateReceived: dateCtrl.text,
                );
                _loadDashboard();
                if (mounted) {
                  messenger.showSnackBar(
                    const SnackBar(content: Text("Fund added!"), backgroundColor: Color(0xFF0F5B44)),
                  );
                }
              } catch (e) {
                if (mounted) {
                  messenger.showSnackBar(
                    SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
                  );
                }
              }
            },
            child: const Text("Add", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Dialog Helpers ─────────────────────────────────────────────────────────

  Widget _dialogTextField(TextEditingController ctrl, String label, IconData icon, {bool isNumber = false}) {
    return TextField(
      controller: ctrl,
      keyboardType: isNumber ? TextInputType.number : TextInputType.text,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: const Color(0xFF0F5B44), size: 20),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.grey.shade50,
      ),
    );
  }

  Widget _dialogDateField(TextEditingController ctrl, String label, BuildContext ctx) {
    return TextField(
      controller: ctrl,
      readOnly: true,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(Icons.calendar_today, color: Color(0xFF0F5B44), size: 20),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.grey.shade50,
      ),
      onTap: () async {
        final dt = await showDatePicker(
          context: ctx,
          initialDate: DateTime.now().add(const Duration(days: 7)),
          firstDate: DateTime(2020),
          lastDate: DateTime(2030),
        );
        if (dt != null) {
          ctrl.text = "${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}";
        }
      },
    );
  }

  // ── Invoice Flow ───────────────────────────────────────────────────────────

  void _handleInvoiceFlow(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
        title: const Center(child: Text("Invoice Source", style: TextStyle(fontWeight: FontWeight.bold))),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("How would you like to add your invoice?", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 25),
            _buildSourceTile(ctx, "Camera Scan", Icons.camera_alt, "Take a photo of your invoice", () => _pickFromCamera(ctx)),
            const SizedBox(height: 12),
            _buildSourceTile(ctx, "Upload Document", Icons.file_present, "Select from Files or PDF", () => _pickFromFiles(ctx)),
          ],
        ),
      ),
    );
  }

  Future<void> _pickFromCamera(BuildContext dialogCtx) async {
    Navigator.pop(dialogCtx);
    try {
      final picker = ImagePicker();
      final XFile? photo = await picker.pickImage(source: ImageSource.camera, imageQuality: 85);
      if (photo != null && mounted) {
        _processOCR(photo.path);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Camera error: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _pickFromFiles(BuildContext dialogCtx) async {
    Navigator.pop(dialogCtx);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
      );
      if (result != null && result.files.isNotEmpty && mounted) {
        _processOCR(result.files.first.path!);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("File picker error: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _processOCR(String path) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator(color: Color(0xFF0F5B44))),
    );

    try {
      final data = await _api.uploadOcr(path);
      if (mounted) {
        Navigator.pop(context); // pop loading
        _showOcrConfirmation(data);
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context); // pop loading
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("OCR Failed: $e"), backgroundColor: Colors.red),
        );
      }
    }
  }

  void _showOcrConfirmation(Map<String, dynamic> data) {
    final vendorCtrl = TextEditingController(text: data['vendor_name'] ?? "");
    final descCtrl = TextEditingController(text: "Invoice #${data['invoice_number'] ?? ''}");
    final amountCtrl = TextEditingController(text: data['amount']?.toString() ?? "");
    final dateCtrl = TextEditingController(text: data['date'] ?? "");
    
    // Suggested type from backend
    bool isReceivable = data['suggested_type'] == 'receivable';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
          title: const Center(child: Text("Confirm Captured Data", style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E)))),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("We extracted the following info. Please verify.", style: TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 20),
                
                // Toggle Button for Receivable vs Payable
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(15)),
                  child: Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setDialogState(() => isReceivable = false),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: !isReceivable ? Colors.red.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Center(
                              child: Text("PAYABLE", style: TextStyle(
                                fontSize: 10, fontWeight: FontWeight.bold, 
                                color: !isReceivable ? Colors.white : Colors.black45
                              )),
                            ),
                          ),
                        ),
                      ),
                      Expanded(
                        child: GestureDetector(
                          onTap: () => setDialogState(() => isReceivable = true),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              color: isReceivable ? Colors.blue.shade700 : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Center(
                              child: Text("RECEIVABLE", style: TextStyle(
                                fontSize: 10, fontWeight: FontWeight.bold, 
                                color: isReceivable ? Colors.white : Colors.black45
                              )),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                
                _dialogTextField(vendorCtrl, isReceivable ? "Client Name" : "Vendor Name", Icons.business),
                const SizedBox(height: 12),
                _dialogTextField(descCtrl, "Description", Icons.description),
                const SizedBox(height: 12),
                _dialogTextField(amountCtrl, "Amount (₹)", Icons.currency_rupee, isNumber: true),
                const SizedBox(height: 12),
                _dialogDateField(dateCtrl, "Due Date", ctx),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0F5B44), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
              onPressed: () async {
                if (amountCtrl.text.isEmpty || dateCtrl.text.isEmpty) return;
                Navigator.pop(ctx);
                setState(() => _isLoading = true);
                try {
                  if (isReceivable) {
                    await _api.createReceivable(
                      clientName: vendorCtrl.text,
                      amount: double.parse(amountCtrl.text),
                      dueDate: dateCtrl.text,
                      description: descCtrl.text,
                    );
                  } else {
                    await _api.createObligation(
                      description: descCtrl.text,
                      amount: double.parse(amountCtrl.text),
                      dueDate: dateCtrl.text,
                      vendorName: vendorCtrl.text.isNotEmpty ? vendorCtrl.text : null,
                    );
                  }
                  
                  _loadDashboard();
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(isReceivable ? "Receivable added!" : "Obligation added!"), 
                        backgroundColor: isReceivable ? Colors.blue.shade700 : const Color(0xFF0F5B44)
                      ),
                    );
                  }
                } catch (e) {
                  setState(() => _isLoading = false);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("Save Error: $e"), backgroundColor: Colors.red),
                    );
                  }
                }
              },
              child: const Text("Confirm & Save", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSourceTile(BuildContext context, String title, IconData icon, String sub, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(15),
      child: Container(
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade200), borderRadius: BorderRadius.circular(15)),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF0F5B44)),
            const SizedBox(width: 15),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.bold)), Text(sub, style: const TextStyle(fontSize: 11, color: Colors.grey))])),
            const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentRecordsSection() {
    if (_dashboardData == null) return const SizedBox.shrink();
    
    final obligations = _dashboardData!['obligations'] as List? ?? [];
    final receivables = _dashboardData!['receivables'] as List? ?? [];
    final funds = _dashboardData!['funds'] as List? ?? [];

    if (obligations.isEmpty && receivables.isEmpty && funds.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Recent Insights", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
        const SizedBox(height: 15),
        if (receivables.isNotEmpty) ...[
          Text("Invoices (Receivables)", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue.shade700)),
          const SizedBox(height: 8),
          ...receivables.take(3).map((r) => _buildRecordItem(r, Colors.blue.shade700)).toList(),
          const SizedBox(height: 15),
        ],
        if (obligations.isNotEmpty) ...[
          Text("Obligations (Payables)", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.red.shade700)),
          const SizedBox(height: 8),
          ...obligations.take(3).map((o) => _buildRecordItem(o, Colors.red.shade700)).toList(),
          const SizedBox(height: 15),
        ],
        if (funds.isNotEmpty) ...[
          const Text("Operating Funds", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black45)),
          const SizedBox(height: 8),
          ...funds.take(3).map((f) => _buildRecordItem(f, const Color(0xFF0F5B44))).toList(),
        ],
      ],
    );
  }

  // ── Overview Tab ───────────────────────────────────────────────────────────

  Widget _buildOverviewTab() {
    return Column(
      children: [
        _buildAppBar(),
        Expanded(
          child: Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.94),
              borderRadius: const BorderRadius.only(topLeft: Radius.circular(35), topRight: Radius.circular(35)),
            ),
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF0F5B44)))
                : _error != null
                    ? _buildErrorView()
                    : RefreshIndicator(
                        onRefresh: _loadDashboard,
                        color: const Color(0xFF0F5B44),
                        child: SingleChildScrollView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.all(25),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _buildSummaryCards(),
                              const SizedBox(height: 25),
                              _buildHealthSection(),
                              const SizedBox(height: 25),
                              _buildRiskSection(),
                              const SizedBox(height: 25),
                              _buildRecommendationCard(),
                              const SizedBox(height: 35),
                              _buildRecentRecordsSection(),
                              const SizedBox(height: 120),
                            ],
                          ),
                        ),
                      ),
          ),
        ),
      ],
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 50, color: Colors.grey),
            const SizedBox(height: 20),
            Text(_error ?? "Something went wrong", textAlign: TextAlign.center, style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 25),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0F5B44)),
              onPressed: _loadDashboard,
              child: const Text("Retry", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 20),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text("Welcome Back,", style: TextStyle(color: Colors.white70, fontSize: 14)),
                Text("CapitalSense", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
              ],
            ),
            GestureDetector(
              onTap: _loadDashboard,
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(15)),
                child: const Icon(Icons.refresh, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Summary Cards ──────────────────────────────────────────────────────────

  Widget _buildSummaryCards() {
    final fs = _dashboardData?['financial_state'] ?? {};
    final balance = (fs['available_balance'] as num?)?.toDouble() ?? 0;
    final cash = (fs['available_cash'] as num?)?.toDouble() ?? 0;
    
    final payablesTotal = (fs['total_payables'] as num?)?.toDouble() ?? 0;
    final receivablesTotal = (fs['total_receivables'] as num?)?.toDouble() ?? 0;

    return Column(
      children: [
        Row(
          children: [
            Expanded(child: _buildLiveMetricCard("BALANCE", _formatCurrency(balance), Icons.account_balance_wallet, const Color(0xFF0F5B44))),
            const SizedBox(width: 12),
            Expanded(child: _buildLiveMetricCard("AVAILABLE", _formatCurrency(cash), Icons.monetization_on, const Color(0xFF1B7A5A))),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(child: _buildLiveMetricCard("RECEIVABLES", _formatCurrency(receivablesTotal), Icons.arrow_upward, Colors.blue.shade700)),
            const SizedBox(width: 12),
            Expanded(child: _buildLiveMetricCard("PAYABLES", _formatCurrency(payablesTotal), Icons.arrow_downward, Colors.red.shade700)),
          ],
        ),
      ],
    );
  }

  Widget _buildLiveMetricCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [BoxShadow(color: color.withOpacity(0.08), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 16),
              const SizedBox(width: 6),
              Flexible(child: Text(label, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.black45, letterSpacing: 0.8))),
            ],
          ),
          const SizedBox(height: 10),
          FittedBox(fit: BoxFit.scaleDown, alignment: Alignment.centerLeft, child: Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color))),
        ],
      ),
    );
  }

  // ── Health Section ─────────────────────────────────────────────────────────

  Widget _buildHealthSection() {
    final fs = _dashboardData?['financial_state'] ?? {};
    final healthScore = (fs['health_score'] as num?)?.toInt() ?? 0;
    final runway = fs['cash_runway_days'];
    final pressure = (fs['obligation_pressure_ratio'] as num?)?.toDouble() ?? 0;
    final bufferDays = (fs['buffer_sufficiency_days'] as num?)?.toDouble();
    final flags = fs['status_flags'] as Map<String, dynamic>? ?? {};

    Color healthColor = healthScore >= 70
        ? const Color(0xFF0F5B44)
        : healthScore >= 40
            ? Colors.orange.shade800
            : Colors.red.shade700;

    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [BoxShadow(color: healthColor.withOpacity(0.08), blurRadius: 15, offset: const Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Financial Health", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(color: healthColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
                child: Text("$healthScore / 100", style: TextStyle(fontWeight: FontWeight.bold, color: healthColor, fontSize: 14)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: healthScore / 100.0,
              backgroundColor: Colors.grey.shade200,
              color: healthColor,
              minHeight: 10,
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(child: _buildMiniStat("Runway", runway != null ? "$runway days" : "Stable", Icons.timer)),
              Expanded(child: _buildMiniStat("Pressure", "${(pressure * 100).toStringAsFixed(0)}%", Icons.speed)),
              Expanded(child: _buildMiniStat("Buffer", bufferDays != null ? "${bufferDays.toStringAsFixed(0)}d" : "—", Icons.shield)),
            ],
          ),
          if (flags.entries.any((e) => e.value == true)) ...[
            const SizedBox(height: 14),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: flags.entries.where((e) => e.value == true).map((e) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(12)),
                  child: Text(
                    e.key.replaceAll('_', ' ').toUpperCase(),
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMiniStat(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 18, color: const Color(0xFF0F5B44)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black45)),
      ],
    );
  }

  // ── Risk Detection Section ─────────────────────────────────────────────────

  Widget _buildRiskSection() {
    final risk = _dashboardData?['risk_detection'];
    if (risk == null) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Risk Projections", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(child: _buildRiskCard("Best", risk['best_case'])),
            const SizedBox(width: 8),
            Expanded(child: _buildRiskCard("Base", risk['base_case'])),
            const SizedBox(width: 8),
            Expanded(child: _buildRiskCard("Worst", risk['worst_case'])),
          ],
        ),
      ],
    );
  }

  Widget _buildRiskCard(String label, Map<String, dynamic>? proj) {
    if (proj == null) return const SizedBox.shrink();
    final severity = proj['risk_severity']?.toString() ?? 'unknown';
    final minCash = (proj['minimum_cash_amount'] as num?)?.toDouble();
    final shortfall = proj['days_to_shortfall'];

    Color sevColor;
    IconData sevIcon;
    switch (severity.toLowerCase()) {
      case 'safe':
        sevColor = const Color(0xFF0F5B44);
        sevIcon = Icons.check_circle;
        break;
      case 'warning':
        sevColor = Colors.orange;
        sevIcon = Icons.warning;
        break;
      case 'critical':
      case 'danger':
        sevColor = Colors.red;
        sevIcon = Icons.dangerous;
        break;
      default:
        sevColor = Colors.grey;
        sevIcon = Icons.help;
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: sevColor.withOpacity(0.3)),
        boxShadow: [BoxShadow(color: sevColor.withOpacity(0.05), blurRadius: 8)],
      ),
      child: Column(
        children: [
          Text(label.toUpperCase(), style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1, color: Colors.grey.shade600)),
          const SizedBox(height: 8),
          Icon(sevIcon, color: sevColor, size: 26),
          const SizedBox(height: 6),
          Text(severity.toUpperCase(), style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: sevColor)),
          if (minCash != null) ...[
            const SizedBox(height: 4),
            Text(_formatCurrency(minCash), style: const TextStyle(fontSize: 10, color: Colors.black45)),
          ],
          if (shortfall != null) ...[
            Text("${shortfall}d", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: sevColor)),
          ],
        ],
      ),
    );
  }

  // ── Recommendation Card ────────────────────────────────────────────────────

  Widget _buildRecommendationCard() {
    final decisions = _dashboardData?['decisions'];
    if (decisions == null) return const SizedBox.shrink();

    final baseCase = decisions['base_case'];
    final strategy = baseCase?['recommended_strategy'] ?? 'N/A';
    final reasoning = baseCase?['reasoning'] ?? '';
    final balanced = baseCase?['balanced'];
    final totalPay = (balanced?['total_payment'] as num?)?.toDouble() ?? 0;
    final cashAfter = (balanced?['estimated_cash_after'] as num?)?.toDouble() ?? 0;
    final survival = (balanced?['survival_probability'] as num?)?.toDouble() ?? 0;

    Color stratColor;
    switch (strategy.toUpperCase()) {
      case 'AGGRESSIVE':
        stratColor = Colors.red.shade600;
        break;
      case 'CONSERVATIVE':
        stratColor = Colors.blue.shade700;
        break;
      default:
        stratColor = const Color(0xFF0F5B44);
    }

    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [stratColor.withOpacity(0.05), Colors.white], begin: Alignment.topLeft, end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(25),
        border: Border.all(color: stratColor.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb, color: stratColor, size: 20),
              const SizedBox(width: 8),
              const Text("AI Recommendation", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0B3B2E))),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(color: stratColor.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: Text(strategy, style: TextStyle(fontWeight: FontWeight.bold, color: stratColor, fontSize: 13, letterSpacing: 1)),
          ),
          const SizedBox(height: 12),
          Text(reasoning, style: const TextStyle(fontSize: 12, color: Colors.black54, height: 1.4)),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildRecommendStat("Pay Now", _formatCurrency(totalPay), stratColor),
              _buildRecommendStat("Cash After", _formatCurrency(cashAfter), const Color(0xFF0F5B44)),
              _buildRecommendStat("Survival", "${survival.toStringAsFixed(0)}%", Colors.blue.shade700),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 9, color: Colors.black45)),
      ],
    );
  }

  // ── Records Tab ────────────────────────────────────────────────────────────

  Widget _buildRecordsTab() {
    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 20),
              child: Row(children: const [
                Icon(Icons.receipt_long, color: Colors.white, size: 26),
                SizedBox(width: 12),
                Text("Audit & Records", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
              ]),
            ),
          ),
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 25, vertical: 10),
            height: 45,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(15),
            ),
            child: TabBar(
              indicator: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
              labelColor: const Color(0xFF0F5B44),
              unselectedLabelColor: Colors.white70,
              labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
              tabs: [
                Tab(text: "PAYABLES (${(_dashboardData?['obligations'] as List?)?.length ?? 0})"),
                Tab(text: "RECEIVABLES (${(_dashboardData?['receivables'] as List?)?.length ?? 0})"),
                Tab(text: "FUNDS (${(_dashboardData?['funds'] as List?)?.length ?? 0})"),
              ],
            ),
          ),
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.94),
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(35), topRight: Radius.circular(35)),
              ),
              child: ClipRRect(
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(35), topRight: Radius.circular(35)),
                child: _dashboardData == null
                  ? const Center(child: CircularProgressIndicator(color: Color(0xFF0F5B44)))
                  : TabBarView(
                      children: [
                         _buildRecordList("Obligations", _dashboardData!['obligations'] as List? ?? [], Colors.red.shade700, Icons.arrow_upward),
                         _buildRecordList("Receivables", _dashboardData!['receivables'] as List? ?? [], Colors.blue.shade700, Icons.arrow_downward),
                         _buildRecordList("Operating Funds", _dashboardData!['funds'] as List? ?? [], const Color(0xFF0F5B44), Icons.account_balance),
                      ],
                    ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecordList(String title, List items, Color color, IconData icon) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 8),
              Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                child: Text("${items.length}", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
              ),
            ],
          ),
          const SizedBox(height: 18),
          if (items.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(top: 100),
                child: Column(
                  children: [
                    Icon(icon, size: 40, color: Colors.grey.shade200),
                    const SizedBox(height: 12),
                    Text("No records found in $title", style: const TextStyle(color: Colors.black38, fontSize: 13)),
                  ],
                ),
              ),
            )
          else
            ...items.map((item) => _buildRecordItem(item, color)).toList(),
          const SizedBox(height: 80),
        ],
      ),
    );
  }


  Widget _buildRecordItem(Map<String, dynamic> item, Color color) {
    final desc = item['description'] ?? item['client_name'] ?? item['source_name'] ?? 'Item';
    final amount = (item['amount'] as num?)?.toDouble() ?? 0;
    final status = item['status'] ?? '';
    final dueDate = item['due_date'] ?? item['date_received'] ?? '';
    
    final isObligation = item.containsKey('amount_paid');
    final isReceivable = item.containsKey('amount_received');
    bool canMark = false;
    if (isObligation) canMark = status != 'paid';
    if (isReceivable) canMark = status != 'received';

    final isTax = desc.toUpperCase().contains('GST') || desc.toUpperCase().contains('TAX') || desc.toUpperCase().contains('TDS');

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: isTax ? Colors.red.shade200 : Colors.grey.shade100, width: isTax ? 1.5 : 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(desc, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    if (isTax) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: Colors.red.shade700, borderRadius: BorderRadius.circular(6)),
                        child: const Text("TAX/LEGAL", style: TextStyle(fontSize: 7, color: Colors.white, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    if (status.isNotEmpty) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(6)),
                        child: Text(status.toString().toUpperCase(), style: TextStyle(fontSize: 9, color: color, fontWeight: FontWeight.bold)),
                      ),
                      const SizedBox(width: 6),
                    ],
                    Text(dueDate, style: const TextStyle(fontSize: 10, color: Colors.black45)),
                  ],
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(_formatCurrency(amount), style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 13)),
              if (canMark) ...[
                const SizedBox(height: 4),
                // Mark Paid / Mark Received button
                GestureDetector(
                  onTap: () => _handleMarkAction(item, isObligation),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      isObligation ? "MARK PAID" : "MARK RECVD",
                      style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                // PAY NOW via Setu — only for obligations
                if (isObligation) ...[
                  const SizedBox(height: 4),
                  GestureDetector(
                    onTap: () => _handleSetuPay(item),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF6A4CE0), Color(0xFF3A77E8)],
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        "PAY NOW",
                        style: TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ],
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _handleMarkAction(Map<String, dynamic> item, bool isObligation) async {
    final total = (item['amount'] as num?)?.toDouble() ?? 0;
    final settledAlready = (isObligation ? item['amount_paid'] : item['amount_received'] as num?)?.toDouble() ?? 0;
    final remaining = total - settledAlready;
    final id = item['id'];
    
    // Optimistic loading
    setState(() => _isLoading = true);
    try {
      if (isObligation) {
        await _api.markObligationPaid(id, remaining, isFull: true);
      } else {
        await _api.markReceivableReceived(id, remaining, isFull: true);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(isObligation ? "✓ Marked as Paid" : "✓ Marked as Received"), backgroundColor: const Color(0xFF0F5B44)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Action failed: $e"), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        _loadDashboard(); // This also clears _isLoading
      }
    }
  }

  Future<void> _handleSetuPay(Map<String, dynamic> item) async {
    final id = item['id'];
    final total = (item['amount'] as num?)?.toDouble() ?? 0;
    final paid = (item['amount_paid'] as num?)?.toDouble() ?? 0;
    final remaining = total - paid;
    if (remaining <= 0) return;

    setState(() => _isLoading = true);
    try {
      final result = await _api.createPaymentLink(id, remaining);
      final paymentLink = result['payment_link'] as String? ?? '';
      if (paymentLink.isNotEmpty) {
        final uri = Uri.parse(paymentLink);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Could not open payment link"), backgroundColor: Colors.red),
            );
          }
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("No payment link returned from Setu"), backgroundColor: Colors.orange),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Payment error: $e"), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ── Bottom Nav ─────────────────────────────────────────────────────────────

  Widget _buildBottomNav() {
    return BottomAppBar(
      shape: const CircularNotchedRectangle(),
      child: SizedBox(
        height: 60,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _navItem(Icons.dashboard, "Dashboard", 0),
            _navItem(Icons.analytics, "Strategy", 1),
            const SizedBox(width: 40),
            _navItem(Icons.receipt_long, "Records", 2),
            _navItem(Icons.settings, "Admin", 3),
          ],
        ),
      ),
    );
  }

  Widget _navItem(IconData icon, String label, int idx) {
    bool isSelected = _selectedTab == idx;
    return InkWell(
      onTap: () => setState(() => _selectedTab = idx),
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: isSelected ? const Color(0xFF0F5B44) : Colors.grey, size: 24),
            Text(label, style: TextStyle(fontSize: 10, color: isSelected ? const Color(0xFF0F5B44) : Colors.grey, fontWeight: isSelected ? FontWeight.bold : FontWeight.normal)),
          ],
        ),
      ),
    );
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  String _formatCurrency(double amount) {
    if (amount >= 10000000) return "₹${(amount / 10000000).toStringAsFixed(1)}Cr";
    if (amount >= 100000) return "₹${(amount / 100000).toStringAsFixed(1)}L";
    if (amount >= 1000) return "₹${(amount / 1000).toStringAsFixed(1)}K";
    return "₹${amount.toStringAsFixed(0)}";
  }
}
