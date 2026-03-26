import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:capitalsense/service/api_service.dart';

class StrategyTab extends StatefulWidget {
  final Map<String, dynamic>? dashboardData;
  final Future<void> Function()? onRefresh;
  const StrategyTab({super.key, this.dashboardData, this.onRefresh});

  @override
  State<StrategyTab> createState() => _StrategyTabState();
}

class _StrategyTabState extends State<StrategyTab>
    with SingleTickerProviderStateMixin {
  final ApiService _api = ApiService();
  late TabController _tabCtrl;

  // Simulation state
  bool _isSimulating = false;
  Map<String, dynamic>? _simResult;
  final _balanceCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _balanceCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildHeader(),
        Expanded(
          child: Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.94),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(35),
                topRight: Radius.circular(35),
              ),
            ),
            child: Column(
              children: [
                const SizedBox(height: 8),
                _buildTabBar(),
                Expanded(
                  child: TabBarView(
                    controller: _tabCtrl,
                    children: [_buildStrategiesView(), _buildSimulationView()],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHeader() {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 25, vertical: 20),
        child: Row(
          children: const [
            Icon(Icons.analytics, color: Colors.white, size: 26),
            SizedBox(width: 12),
            Text(
              "Strategy & Simulations",
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 25),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(16),
      ),
      child: TabBar(
        controller: _tabCtrl,
        indicator: BoxDecoration(
          color: const Color(0xFF0F5B44),
          borderRadius: BorderRadius.circular(14),
        ),
        labelColor: Colors.white,
        unselectedLabelColor: Colors.black54,
        labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
        tabs: const [
          Tab(text: "Payment Strategies"),
          Tab(text: "What-If Simulator"),
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // STRATEGIES VIEW
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildStrategiesView() {
    final decisions = widget.dashboardData?['decisions'];
    if (decisions == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(40),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.info_outline, size: 40, color: Colors.grey),
              SizedBox(height: 12),
              Text(
                "No strategy data yet",
                style: TextStyle(color: Colors.black54),
              ),
              SizedBox(height: 6),
              Text(
                "Add obligations and funds to generate strategies",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.black38, fontSize: 12),
              ),
            ],
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildOverallRecommendation(
            decisions['overall_recommendation'] ?? '',
          ),
          const SizedBox(height: 20),
          _buildScenarioSection(
            "BASE CASE",
            decisions['base_case'],
            const Color(0xFF0F5B44),
          ),
          const SizedBox(height: 16),
          _buildScenarioSection(
            "BEST CASE",
            decisions['best_case'],
            Colors.blue.shade700,
          ),
          const SizedBox(height: 16),
          _buildScenarioSection(
            "WORST CASE",
            decisions['worst_case'],
            Colors.red.shade700,
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildOverallRecommendation(String text) {
    final lines = text.split('\n').where((l) => l.trim().isNotEmpty).toList();
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [const Color(0xFF0F5B44).withOpacity(0.06), Colors.white],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF0F5B44).withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.auto_awesome,
                color: const Color(0xFF0F5B44),
                size: 18,
              ),
              const SizedBox(width: 8),
              const Text(
                "Overall Recommendation",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: Color(0xFF0B3B2E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...lines
              .take(8)
              .map(
                (line) => Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text(
                    line.trim(),
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.black54,
                      fontWeight: line.contains('===') || line.contains('Case')
                          ? FontWeight.bold
                          : FontWeight.normal,
                    ),
                  ),
                ),
              ),
        ],
      ),
    );
  }

  Widget _buildScenarioSection(
    String title,
    Map<String, dynamic>? data,
    Color color,
  ) {
    if (data == null) return const SizedBox.shrink();

    final recommended = data['recommended_strategy'] ?? '';
    final reasoning = data['reasoning'] ?? '';
    final cashAvail = (data['cash_available'] as num?)?.toDouble();

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: color.withOpacity(0.15)),
        color: Colors.white,
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 16),
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.assessment, color: color, size: 20),
          ),
          title: Text(
            title,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: color,
              fontSize: 14,
            ),
          ),
          subtitle: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  recommended,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ),
              if (cashAvail != null) ...[
                const SizedBox(width: 8),
                Text(
                  _formatCurrency(cashAvail),
                  style: const TextStyle(fontSize: 11, color: Colors.black45),
                ),
              ],
            ],
          ),
          initiallyExpanded: title == "BASE CASE",
          children: [
            _buildReasoningPanel(reasoning, color),
            const SizedBox(height: 12),
            _buildStrategyComparison(data, color),
          ],
        ),
      ),
    );
  }

  Widget _buildReasoningPanel(String reasoning, Color color) {
    final items = _extractReasoningPoints(reasoning);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.12)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.fact_check, size: 16, color: color),
              const SizedBox(width: 8),
              Text(
                "Why This Case Recommends It",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...items
              .take(4)
              .map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        margin: const EdgeInsets.only(top: 6),
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          item,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF30443E),
                            height: 1.5,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
        ],
      ),
    );
  }

  List<String> _extractReasoningPoints(String reasoning) {
    final normalized = reasoning.replaceAll('\r', '\n').trim();
    if (normalized.isEmpty) return const ["No explanation was returned."];

    final lineParts = normalized
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty && !line.contains('==='))
        .toList();
    if (lineParts.length > 1) return lineParts;

    final sentenceParts = normalized
        .split(RegExp(r'(?<=[.!?])\s+'))
        .map((part) => part.trim())
        .where((part) => part.isNotEmpty)
        .toList();
    return sentenceParts.isEmpty ? [normalized] : sentenceParts;
  }

  Widget _buildStrategyComparison(
    Map<String, dynamic> scenario,
    Color baseColor,
  ) {
    final strategies = [
      {
        "key": "aggressive",
        "label": "Aggressive",
        "icon": Icons.flash_on,
        "color": Colors.red.shade600,
      },
      {
        "key": "balanced",
        "label": "Balanced",
        "icon": Icons.balance,
        "color": const Color(0xFF0F5B44),
      },
    ];

    final recommended = (scenario['recommended_strategy'] ?? '')
        .toString()
        .toUpperCase();

    return Column(
      children: strategies.map((s) {
        final data = scenario[s['key']] as Map<String, dynamic>?;
        if (data == null) return const SizedBox.shrink();
        final isRecommended =
            (s['label'] as String).toUpperCase() == recommended;

        final totalPay = (data['total_payment'] as num?)?.toDouble() ?? 0;
        final penalty = (data['total_penalty_cost'] as num?)?.toDouble() ?? 0;
        final cashAfter =
            (data['estimated_cash_after'] as num?)?.toDouble() ?? 0;
        final survival =
            (data['survival_probability'] as num?)?.toDouble() ?? 0;
        final rawDecisions = data['decisions'] as List? ?? [];
        final decisions = _sortDecisionItems(rawDecisions);

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: isRecommended
                ? (s['color'] as Color).withOpacity(0.04)
                : Colors.grey.shade50,
            border: Border.all(
              color: isRecommended
                  ? (s['color'] as Color).withOpacity(0.3)
                  : Colors.grey.shade200,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    s['icon'] as IconData,
                    size: 16,
                    color: s['color'] as Color,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    s['label'] as String,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: s['color'] as Color,
                    ),
                  ),
                  if (isRecommended) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: (s['color'] as Color).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        "★ PICK",
                        style: TextStyle(
                          fontSize: 8,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildStratStat(
                    "Pay",
                    _formatCurrency(totalPay),
                    s['color'] as Color,
                  ),
                  _buildStratStat(
                    "Penalty",
                    _formatCurrency(penalty),
                    penalty > 0 ? Colors.red : Colors.green,
                  ),
                  _buildStratStat(
                    "Cash After",
                    _formatCurrency(cashAfter),
                    const Color(0xFF0F5B44),
                  ),
                  _buildStratStat(
                    "Survival",
                    "${survival.toStringAsFixed(0)}%",
                    survival >= 80 ? Colors.green : Colors.orange,
                  ),
                ],
              ),
              if (decisions.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Divider(height: 1),
                const SizedBox(height: 8),
                ...decisions.map(
                  (d) =>
                      _buildDecisionItem(Map<String, dynamic>.from(d as Map)),
                ),
              ],
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildStratStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(label, style: const TextStyle(fontSize: 8, color: Colors.black38)),
      ],
    );
  }

  Widget _buildDecisionItem(Map<String, dynamic> d) {
    final obligationId = (d['obligation_id'] ?? '').toString();
    final obligationStatus = _obligationStatus(obligationId);
    final status = d['status']?.toString() ?? '';
    final payAmount = (d['pay_amount'] as num?)?.toDouble() ?? 0;
    final vendorName = d['vendor_name'] ?? obligationId;
    final rationale = d['rationale'] ?? '';
    final delayDays = d['delay_days'] as int? ?? 0;
    final dueDate = d['due_date']?.toString() ?? '';
    final isDeferred = obligationStatus == 'deferred';

    Color statusColor;
    IconData statusIcon;
    switch (status) {
      case 'PAY_IN_FULL':
        statusColor = Colors.green;
        statusIcon = Icons.check_circle;
        break;
      case 'PARTIAL_PAY':
        statusColor = Colors.orange;
        statusIcon = Icons.timelapse;
        break;
      case 'DELAY':
        statusColor = Colors.red.shade400;
        statusIcon = Icons.schedule;
        break;
      case 'STRATEGIC_DEFAULT':
        statusColor = Colors.red;
        statusIcon = Icons.block;
        break;
      default:
        statusColor = Colors.grey;
        statusIcon = Icons.help;
    }

    final isTax =
        vendorName.toUpperCase().contains('GST') ||
        vendorName.toUpperCase().contains('TAX') ||
        vendorName.toUpperCase().contains('TDS') ||
        rationale.toUpperCase().contains('LEGAL');

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: statusColor.withOpacity(0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isTax ? Colors.red.shade400 : statusColor.withOpacity(0.15),
          width: isTax ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(statusIcon, size: 16, color: statusColor),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          vendorName,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                        if (isTax) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 5,
                              vertical: 1,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.red.shade700,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              "TAX/LEGAL",
                              style: TextStyle(
                                fontSize: 7,
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    Text(
                      "${status.replaceAll('_', ' ')}${delayDays > 0 ? ' (+$delayDays days)' : ''} • $rationale",
                      style: TextStyle(
                        fontSize: 9,
                        color: statusColor,
                        height: 1.3,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Text(
                _formatCurrency(payAmount),
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                  color: statusColor,
                ),
              ),
            ],
          ),
          if (!isTax) ...[
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: isDeferred
                  ? Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(
                            Icons.check_circle_outline,
                            size: 12,
                            color: Colors.black38,
                          ),
                          SizedBox(width: 5),
                          Text(
                            "Email Sent",
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Colors.black38,
                            ),
                          ),
                        ],
                      ),
                    )
                  : GestureDetector(
                      onTap: obligationId.isEmpty
                          ? null
                          : () => _showDeferralDialog(
                              obligationId: obligationId,
                              vendorName: vendorName,
                              amount: payAmount,
                              dueDate: dueDate,
                            ),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 5,
                        ),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF6B3FA0), Color(0xFF9B5DE5)],
                          ),
                          borderRadius: BorderRadius.circular(8),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF6B3FA0).withOpacity(0.3),
                              blurRadius: 6,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            Icon(
                              Icons.forward_to_inbox,
                              size: 12,
                              color: Colors.white,
                            ),
                            SizedBox(width: 5),
                            Text(
                              "Defer Payment",
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                                letterSpacing: 0.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Deferral Dialog & Webhook ───────────────────────────────────────────────

  Future<void> _showDeferralDialog({
    required String obligationId,
    required String vendorName,
    required double amount,
    required String dueDate,
  }) async {
    final vendorCtrl = TextEditingController(text: vendorName);
    final amountCtrl = TextEditingController(
      text: amount > 0 ? amount.toStringAsFixed(2) : '',
    );
    final dueDateCtrl = TextEditingController(text: dueDate);
    final proposedCtrl = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
        title: Row(
          children: const [
            Icon(Icons.forward_to_inbox, color: Color(0xFF6B3FA0), size: 22),
            SizedBox(width: 10),
            Text(
              "Defer Payment",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                "Review or fill in the details below. An email draft will be sent to the vendor requesting deferral.",
                style: TextStyle(fontSize: 12, color: Colors.black54),
              ),
              const SizedBox(height: 16),
              _dialogField(vendorCtrl, "Vendor Name", Icons.business),
              const SizedBox(height: 12),
              _dialogField(
                amountCtrl,
                "Amount (₹)",
                Icons.currency_rupee,
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 12),
              _dialogField(dueDateCtrl, "Due Date (YYYY-MM-DD)", Icons.event),
              const SizedBox(height: 12),
              _dialogField(
                proposedCtrl,
                "Proposed New Date (YYYY-MM-DD) — optional",
                Icons.event_available,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text(
              "Cancel",
              style: TextStyle(color: Colors.black45),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF6B3FA0),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            onPressed: () {
              if (vendorCtrl.text.trim().isEmpty ||
                  amountCtrl.text.trim().isEmpty ||
                  dueDateCtrl.text.trim().isEmpty) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(
                    content: Text(
                      "Please fill Vendor Name, Amount and Due Date.",
                    ),
                    backgroundColor: Colors.red,
                    duration: Duration(seconds: 2),
                  ),
                );
                return;
              }
              Navigator.pop(ctx, true);
            },
            child: const Text(
              "Send Deferral",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    await _sendDeferral(
      obligationId: obligationId,
      vendorName: vendorCtrl.text.trim(),
      amount: double.tryParse(amountCtrl.text.trim()) ?? 0,
      dueDate: dueDateCtrl.text.trim(),
      proposedDate: proposedCtrl.text.trim().isNotEmpty
          ? proposedCtrl.text.trim()
          : null,
    );
  }

  Widget _dialogField(
    TextEditingController ctrl,
    String label,
    IconData icon, {
    TextInputType keyboardType = TextInputType.text,
  }) {
    return TextField(
      controller: ctrl,
      keyboardType: keyboardType,
      style: const TextStyle(fontSize: 13),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(fontSize: 12),
        prefixIcon: Icon(icon, size: 18, color: const Color(0xFF6B3FA0)),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF9B5DE5), width: 1.5),
        ),
        filled: true,
        fillColor: Colors.grey.shade50,
        contentPadding: const EdgeInsets.symmetric(
          vertical: 10,
          horizontal: 12,
        ),
      ),
    );
  }

  Future<void> _sendDeferral({
    required String obligationId,
    required String vendorName,
    required double amount,
    required String dueDate,
    String? proposedDate,
  }) async {
    const webhookUrl =
        'https://n8n.kushvinth.com/webhook-test/47f07c2a-8146-455f-9beb-b7fedcaa314f';
    final messenger = ScaffoldMessenger.of(context);

    if (!mounted) return;
    messenger.showSnackBar(
      const SnackBar(
        content: Row(
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                color: Colors.white,
                strokeWidth: 2,
              ),
            ),
            SizedBox(width: 12),
            Text("Sending deferral email…"),
          ],
        ),
        duration: Duration(seconds: 30),
        backgroundColor: Color(0xFF6B3FA0),
      ),
    );

    try {
      final body = <String, dynamic>{
        'vendor_name': vendorName,
        'amount': amount,
        'due_date': dueDate,
      };
      if (proposedDate != null) body['proposed_date'] = proposedDate;

      final response = await http.post(
        Uri.parse(webhookUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );

      if (!mounted) return;
      messenger.hideCurrentSnackBar();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        // Now update the obligation status to deferred in our backend
        try {
          await _api.deferObligation(obligationId);
          await widget.onRefresh?.call();
        } catch (e) {
          debugPrint("Failed to update status: $e");
        }

        if (!mounted) return;
        messenger.showSnackBar(
          const SnackBar(
            content: Text("Deferral email sent successfully!"),
            backgroundColor: Color(0xFF0F5B44),
          ),
        );
        _showSuccessBanner(obligationId);
      } else {
        messenger.showSnackBar(
          SnackBar(
            content: Text("Failed to send email: ${response.statusCode}"),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(
          content: Text("Connection error: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showSuccessBanner(String emailId) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        contentPadding: EdgeInsets.zero,
        content: Container(
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            gradient: const LinearGradient(
              colors: [Color(0xFF6B3FA0), Color(0xFF9B5DE5)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.mark_email_read,
                  color: Colors.white,
                  size: 36,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                "Email Sent!",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "The deferral request email has been successfully drafted and sent to the vendor.",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  height: 1.5,
                ),
              ),
              if (emailId.isNotEmpty) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    "Message ID: $emailId",
                    style: const TextStyle(
                      color: Colors.white60,
                      fontSize: 10,
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF6B3FA0),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text(
                    "Done",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<dynamic> _sortDecisionItems(List decisions) {
    final sortable = decisions
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
    sortable.sort((a, b) {
      final leftId = (a['obligation_id'] ?? '').toString();
      final rightId = (b['obligation_id'] ?? '').toString();
      final leftRank = _decisionRank(leftId);
      final rightRank = _decisionRank(rightId);
      if (leftRank != rightRank) return leftRank.compareTo(rightRank);

      final leftDue = _obligationDueDate(leftId);
      final rightDue = _obligationDueDate(rightId);
      if (leftDue != null && rightDue != null) {
        final dueCompare = leftDue.compareTo(rightDue);
        if (dueCompare != 0) return dueCompare;
      } else if (leftDue != null) {
        return -1;
      } else if (rightDue != null) {
        return 1;
      }

      final leftPay = (a['pay_amount'] as num?)?.toDouble() ?? 0;
      final rightPay = (b['pay_amount'] as num?)?.toDouble() ?? 0;
      return rightPay.compareTo(leftPay);
    });
    return sortable;
  }

  int _decisionRank(String obligationId) {
    switch (_obligationStatus(obligationId)) {
      case 'overdue':
        return 0;
      case 'pending':
      case 'partially_paid':
        return 1;
      case 'deferred':
        return 2;
      case 'paid':
        return 3;
      default:
        return 1;
    }
  }

  String? _obligationStatus(String obligationId) {
    if (obligationId.isEmpty) return null;
    final obligations =
        widget.dashboardData?['obligations'] as List? ?? const [];
    for (final item in obligations) {
      final obligation = item as Map;
      if ((obligation['id'] ?? '').toString() == obligationId) {
        return obligation['status']?.toString();
      }
    }
    return null;
  }

  DateTime? _obligationDueDate(String obligationId) {
    if (obligationId.isEmpty) return null;
    final obligations =
        widget.dashboardData?['obligations'] as List? ?? const [];
    for (final item in obligations) {
      final obligation = item as Map;
      if ((obligation['id'] ?? '').toString() == obligationId) {
        final rawDueDate = obligation['due_date']?.toString();
        return rawDueDate == null ? null : DateTime.tryParse(rawDueDate);
      }
    }
    return null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SIMULATION VIEW
  // ══════════════════════════════════════════════════════════════════════════

  Widget _buildSimulationView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSimulationForm(),
          const SizedBox(height: 20),
          if (_isSimulating)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(30),
                child: CircularProgressIndicator(color: Color(0xFF0F5B44)),
              ),
            ),
          if (_simResult != null && !_isSimulating) _buildSimulationResults(),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  Widget _buildSimulationForm() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 12),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.science, color: Color(0xFF0F5B44), size: 20),
              const SizedBox(width: 8),
              const Text(
                "What-If Scenario",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(0xFF0B3B2E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            "Simulate the payment outlook for a different cash balance.",
            style: TextStyle(fontSize: 11, color: Colors.black45),
          ),
          const SizedBox(height: 18),
          TextField(
            controller: _balanceCtrl,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: "Cash Balance Override (₹)",
              hintText: "Leave empty for current balance",
              prefixIcon: const Icon(
                Icons.currency_rupee,
                color: Color(0xFF0F5B44),
                size: 20,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              filled: true,
              fillColor: Colors.grey.shade50,
            ),
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Text(
              "The simulator uses the platform's default recommendation logic for the entered balance.",
              style: TextStyle(
                fontSize: 11,
                color: Colors.black54,
                height: 1.45,
              ),
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0F5B44),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              icon: const Icon(Icons.play_arrow, color: Colors.white),
              label: const Text(
                "Run Simulation",
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
              onPressed: _isSimulating ? null : _runSimulation,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _runSimulation() async {
    setState(() {
      _isSimulating = true;
      _simResult = null;
    });
    try {
      final result = await _api.simulateScenario(
        balance: _balanceCtrl.text.isNotEmpty
            ? double.tryParse(_balanceCtrl.text)
            : null,
      );
      if (mounted) setState(() => _simResult = result);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Simulation error: $e"),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSimulating = false);
    }
  }

  Widget _buildSimulationResults() {
    final healthScore = (_simResult?['health_score'] as num?)?.toInt() ?? 0;
    final runway = _simResult?['cash_runway_days'];
    final recommendation = _simResult?['recommendation'] ?? '';
    final overallRec = _simResult?['overall_recommendation'] ?? '';
    final overrides =
        _simResult?['scenario_overrides'] as Map<String, dynamic>? ?? {};
    final selectedAppetite = (_simResult?['selected_appetite'] ?? 'MODERATE')
        .toString();
    final comparisonAppetite =
        (_simResult?['comparison_appetite'] ?? 'AGGRESSIVE').toString();
    final selectedStrategy =
        _simResult?['selected_strategy'] as Map<String, dynamic>? ?? {};
    final comparisonStrategy =
        _simResult?['comparison_strategy'] as Map<String, dynamic>? ?? {};
    final difference =
        _simResult?['appetite_difference'] as Map<String, dynamic>? ?? {};
    final selectedDecisions =
        selectedStrategy['decisions'] as List? ?? const [];

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
        border: Border.all(color: healthColor.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(color: healthColor.withOpacity(0.08), blurRadius: 12),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.insights, color: Color(0xFF0B3B2E), size: 20),
              const SizedBox(width: 8),
              const Text(
                "Simulation Results",
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(0xFF0B3B2E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Scenario overrides tag
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: overrides.entries.map((e) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  "${e.key}: ${e.value}",
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),

          // Health + Runway row
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: healthColor.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Text(
                        "${(_simResult?['projected_health_score'] ?? healthScore)}",
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: healthColor,
                        ),
                      ),
                      const Text(
                        "Projected Health",
                        style: TextStyle(fontSize: 10, color: Colors.black45),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _simResult?['projected_runway_days'] != null
                            ? "${_simResult!['projected_runway_days']}"
                            : (runway != null ? "$runway" : "∞"),
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue.shade700,
                        ),
                      ),
                      const Text(
                        "Projected Runway",
                        style: TextStyle(fontSize: 10, color: Colors.black45),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          _buildSimulationSummaryBanner(
            selectedAppetite: selectedAppetite,
            comparisonAppetite: comparisonAppetite,
            recommendation: recommendation,
            difference: difference,
            color: healthColor,
          ),
          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildSimulationStrategyCard(
                  title: "$selectedAppetite Appetite",
                  subtitle: "Selected for this run",
                  strategy: selectedStrategy,
                  accent: healthColor,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildSimulationStrategyCard(
                  title: "$comparisonAppetite View",
                  subtitle: "Closest alternative",
                  strategy: comparisonStrategy,
                  accent: Colors.blue.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (selectedDecisions.isNotEmpty) ...[
            _buildSimulationActions(
              selectedAppetite,
              selectedDecisions,
              healthColor,
            ),
            const SizedBox(height: 16),
          ],

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: healthColor.withOpacity(0.06),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: healthColor.withOpacity(0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.lightbulb, color: healthColor, size: 18),
                    const SizedBox(width: 8),
                    Text(
                      "RECOMMENDED: $recommendation",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: healthColor,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
                if (_simResult?['strategy_metrics'] != null) ...[
                  const SizedBox(height: 12),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  const Text(
                    "IMPACT OF THIS STRATEGY",
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Colors.black45,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildMetricMini(
                        "Total Pay",
                        _formatCurrency(
                          _simResult!['strategy_metrics']['total_payment'],
                        ),
                      ),
                      _buildMetricMini(
                        "Penalties",
                        _formatCurrency(
                          _simResult!['strategy_metrics']['penalty_cost'],
                        ),
                        color: Colors.red.shade700,
                      ),
                      _buildMetricMini(
                        "Survives?",
                        "${(_simResult!['strategy_metrics']['survival_probability'] as num).toInt()}%",
                        color: Colors.blue.shade700,
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Text(
              overallRec.length > 500
                  ? "${overallRec.substring(0, 500)}..."
                  : overallRec,
              style: const TextStyle(
                fontSize: 11,
                color: Colors.black54,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSimulationSummaryBanner({
    required String selectedAppetite,
    required String comparisonAppetite,
    required String recommendation,
    required Map<String, dynamic> difference,
    required Color color,
  }) {
    final isIdentical = difference['is_identical'] == true;
    final cashDelta = (difference['cash_after_delta'] as num?)?.toDouble() ?? 0;
    final penaltyDelta = (difference['penalty_delta'] as num?)?.toDouble() ?? 0;
    final survivalDelta =
        (difference['survival_delta'] as num?)?.toDouble() ?? 0;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.tune, color: color, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  "$selectedAppetite appetite selected",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: color,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            "Strategy chosen: $recommendation",
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF0B3B2E),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            isIdentical
                ? "$selectedAppetite and $comparisonAppetite produce the same result for this cash balance."
                : "$selectedAppetite differs from $comparisonAppetite by ${_formatSignedCurrency(cashDelta)} cash-after, ${_formatSignedCurrency(penaltyDelta)} penalties, and ${_formatSignedPercent(survivalDelta)} survival.",
            style: const TextStyle(
              fontSize: 11,
              color: Colors.black54,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSimulationStrategyCard({
    required String title,
    required String subtitle,
    required Map<String, dynamic> strategy,
    required Color accent,
  }) {
    final name = (strategy['name'] ?? 'N/A').toString();
    final totalPayment = strategy['total_payment'];
    final penaltyCost = strategy['penalty_cost'];
    final cashAfter = strategy['cash_after'];
    final survival =
        (strategy['survival_probability'] as num?)?.toDouble() ?? 0;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: accent.withOpacity(0.16)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: accent,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 10, color: Colors.black45),
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
            decoration: BoxDecoration(
              color: accent.withOpacity(0.08),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              name,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: accent,
                letterSpacing: 0.4,
              ),
            ),
          ),
          const SizedBox(height: 12),
          _buildMetricMini(
            "Pay Now",
            _formatCurrency(totalPayment),
            color: accent,
          ),
          const SizedBox(height: 8),
          _buildMetricMini(
            "Penalty Cost",
            _formatCurrency(penaltyCost),
            color: Colors.red.shade700,
          ),
          const SizedBox(height: 8),
          _buildMetricMini(
            "Cash After",
            _formatCurrency(cashAfter),
            color: const Color(0xFF0F5B44),
          ),
          const SizedBox(height: 8),
          _buildMetricMini(
            "Survival",
            "${survival.toStringAsFixed(0)}%",
            color: Colors.blue.shade700,
          ),
        ],
      ),
    );
  }

  Widget _buildSimulationActions(
    String appetite,
    List decisions,
    Color accent,
  ) {
    final topItems =
        decisions.map((item) => Map<String, dynamic>.from(item as Map)).toList()
          ..sort((a, b) {
            final leftAmount = (a['pay_amount'] as num?)?.toDouble() ?? 0;
            final rightAmount = (b['pay_amount'] as num?)?.toDouble() ?? 0;
            return rightAmount.compareTo(leftAmount);
          });

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Top Actions Under $appetite",
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Color(0xFF0B3B2E),
            ),
          ),
          const SizedBox(height: 10),
          ...topItems.take(4).map((decision) {
            final vendor =
                (decision['vendor_name'] ?? decision['obligation_id'] ?? '')
                    .toString();
            final status = (decision['status'] ?? 'N/A').toString().replaceAll(
              '_',
              ' ',
            );
            final rationale = (decision['rationale'] ?? '').toString();
            final payAmount = decision['pay_amount'];
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    margin: const EdgeInsets.only(top: 5),
                    decoration: BoxDecoration(
                      color: accent,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          vendor,
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          "$status • ${rationale.isEmpty ? 'No rationale provided' : rationale}",
                          style: const TextStyle(
                            fontSize: 10,
                            color: Colors.black54,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatCurrency(payAmount),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: accent,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildMetricMini(String label, String value, {Color? color}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 9,
            color: Colors.black38,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: color ?? const Color(0xFF0F5B44),
          ),
        ),
      ],
    );
  }

  String _formatCurrency(dynamic val) {
    if (val == null) return "₹0.00";
    final n = (val as num).toDouble();
    if (n >= 10000000) return "₹${(n / 10000000).toStringAsFixed(1)}Cr";
    if (n >= 100000) return "₹${(n / 100000).toStringAsFixed(1)}L";
    if (n >= 1000) return "₹${(n / 1000).toStringAsFixed(1)}K";
    return "₹${n.toStringAsFixed(0)}";
  }

  String _formatSignedCurrency(double amount) {
    final prefix = amount > 0 ? "+" : "";
    return "$prefix${_formatCurrency(amount)}";
  }

  String _formatSignedPercent(double amount) {
    final prefix = amount > 0 ? "+" : "";
    return "$prefix${amount.toStringAsFixed(0)}%";
  }
}
