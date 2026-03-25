import 'package:flutter/material.dart';
import 'package:capitalsense/service/api_service.dart';

class StrategyTab extends StatefulWidget {
  final Map<String, dynamic>? dashboardData;
  const StrategyTab({super.key, this.dashboardData});

  @override
  State<StrategyTab> createState() => _StrategyTabState();
}

class _StrategyTabState extends State<StrategyTab> with SingleTickerProviderStateMixin {
  final ApiService _api = ApiService();
  late TabController _tabCtrl;

  // Simulation state
  bool _isSimulating = false;
  Map<String, dynamic>? _simResult;
  final _balanceCtrl = TextEditingController();
  String _riskLevel = "MODERATE";

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
              borderRadius: const BorderRadius.only(topLeft: Radius.circular(35), topRight: Radius.circular(35)),
            ),
            child: Column(
              children: [
                const SizedBox(height: 8),
                _buildTabBar(),
                Expanded(
                  child: TabBarView(
                    controller: _tabCtrl,
                    children: [
                      _buildStrategiesView(),
                      _buildSimulationView(),
                    ],
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
        child: Row(children: const [
          Icon(Icons.analytics, color: Colors.white, size: 26),
          SizedBox(width: 12),
          Text("Strategy & Simulations", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
        ]),
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
              Text("No strategy data yet", style: TextStyle(color: Colors.black54)),
              SizedBox(height: 6),
              Text("Add obligations and funds to generate strategies", textAlign: TextAlign.center, style: TextStyle(color: Colors.black38, fontSize: 12)),
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
          _buildOverallRecommendation(decisions['overall_recommendation'] ?? ''),
          const SizedBox(height: 20),
          _buildScenarioSection("BASE CASE", decisions['base_case'], const Color(0xFF0F5B44)),
          const SizedBox(height: 16),
          _buildScenarioSection("BEST CASE", decisions['best_case'], Colors.blue.shade700),
          const SizedBox(height: 16),
          _buildScenarioSection("WORST CASE", decisions['worst_case'], Colors.red.shade700),
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
              Icon(Icons.auto_awesome, color: const Color(0xFF0F5B44), size: 18),
              const SizedBox(width: 8),
              const Text("Overall Recommendation", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF0B3B2E))),
            ],
          ),
          const SizedBox(height: 10),
          ...lines.take(8).map((line) => Padding(
                padding: const EdgeInsets.only(bottom: 3),
                child: Text(
                  line.trim(),
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.black54,
                    fontWeight: line.contains('===') || line.contains('Case') ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildScenarioSection(String title, Map<String, dynamic>? data, Color color) {
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
            decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(Icons.assessment, color: color, size: 20),
          ),
          title: Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14)),
          subtitle: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(8)),
                child: Text(recommended, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color)),
              ),
              if (cashAvail != null) ...[
                const SizedBox(width: 8),
                Text(_formatCurrency(cashAvail), style: const TextStyle(fontSize: 11, color: Colors.black45)),
              ],
            ],
          ),
          initiallyExpanded: title == "BASE CASE",
          children: [
            Text(reasoning, style: const TextStyle(fontSize: 11, color: Colors.black45, height: 1.4)),
            const SizedBox(height: 12),
            _buildStrategyComparison(data, color),
          ],
        ),
      ),
    );
  }

  Widget _buildStrategyComparison(Map<String, dynamic> scenario, Color baseColor) {
    final strategies = [
      {"key": "aggressive", "label": "Aggressive", "icon": Icons.flash_on, "color": Colors.red.shade600},
      {"key": "balanced", "label": "Balanced", "icon": Icons.balance, "color": const Color(0xFF0F5B44)},
      {"key": "conservative", "label": "Conservative", "icon": Icons.shield, "color": Colors.blue.shade700},
    ];

    final recommended = (scenario['recommended_strategy'] ?? '').toString().toUpperCase();

    return Column(
      children: strategies.map((s) {
        final data = scenario[s['key']] as Map<String, dynamic>?;
        if (data == null) return const SizedBox.shrink();
        final isRecommended = (s['label'] as String).toUpperCase() == recommended;

        final totalPay = (data['total_payment'] as num?)?.toDouble() ?? 0;
        final penalty = (data['total_penalty_cost'] as num?)?.toDouble() ?? 0;
        final cashAfter = (data['estimated_cash_after'] as num?)?.toDouble() ?? 0;
        final survival = (data['survival_probability'] as num?)?.toDouble() ?? 0;
        final decisions = data['decisions'] as List? ?? [];

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: isRecommended ? (s['color'] as Color).withOpacity(0.04) : Colors.grey.shade50,
            border: Border.all(color: isRecommended ? (s['color'] as Color).withOpacity(0.3) : Colors.grey.shade200),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(s['icon'] as IconData, size: 16, color: s['color'] as Color),
                  const SizedBox(width: 6),
                  Text(s['label'] as String, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: s['color'] as Color)),
                  if (isRecommended) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(color: (s['color'] as Color).withOpacity(0.15), borderRadius: BorderRadius.circular(6)),
                      child: const Text("★ PICK", style: TextStyle(fontSize: 8, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildStratStat("Pay", _formatCurrency(totalPay), s['color'] as Color),
                  _buildStratStat("Penalty", _formatCurrency(penalty), penalty > 0 ? Colors.red : Colors.green),
                  _buildStratStat("Cash After", _formatCurrency(cashAfter), const Color(0xFF0F5B44)),
                  _buildStratStat("Survival", "${survival.toStringAsFixed(0)}%", survival >= 80 ? Colors.green : Colors.orange),
                ],
              ),
              if (decisions.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Divider(height: 1),
                const SizedBox(height: 8),
                ...decisions.map((d) => _buildDecisionItem(d)),
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
        Text(value, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
        Text(label, style: const TextStyle(fontSize: 8, color: Colors.black38)),
      ],
    );
  }

  Widget _buildDecisionItem(Map<String, dynamic> d) {
    final status = d['status']?.toString() ?? '';
    final payAmount = (d['pay_amount'] as num?)?.toDouble() ?? 0;
    final vendorName = d['vendor_name'] ?? d['obligation_id'] ?? '';
    final rationale = d['rationale'] ?? '';
    final delayDays = d['delay_days'] as int? ?? 0;

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

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: statusColor.withOpacity(0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: statusColor.withOpacity(0.15)),
      ),
      child: Row(
        children: [
          Icon(statusIcon, size: 16, color: statusColor),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(vendorName, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11)),
                Text(
                  "${status.replaceAll('_', ' ')}${delayDays > 0 ? ' (+$delayDays days)' : ''} • $rationale",
                  style: TextStyle(fontSize: 9, color: statusColor, height: 1.3),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Text(_formatCurrency(payAmount), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: statusColor)),
        ],
      ),
    );
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
          if (_isSimulating) const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator(color: Color(0xFF0F5B44)))),
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
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 12)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.science, color: Color(0xFF0F5B44), size: 20),
              const SizedBox(width: 8),
              const Text("What-If Scenario", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF0B3B2E))),
            ],
          ),
          const SizedBox(height: 6),
          const Text("Simulate different cash positions and risk appetites", style: TextStyle(fontSize: 11, color: Colors.black45)),
          const SizedBox(height: 18),
          TextField(
            controller: _balanceCtrl,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: "Cash Balance Override (₹)",
              hintText: "Leave empty for current balance",
              prefixIcon: const Icon(Icons.currency_rupee, color: Color(0xFF0F5B44), size: 20),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
              filled: true,
              fillColor: Colors.grey.shade50,
            ),
          ),
          const SizedBox(height: 14),
          const Text("Risk Appetite", style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black54)),
          const SizedBox(height: 8),
          Row(
            children: ["AGGRESSIVE", "MODERATE", "CONSERVATIVE"].map((level) {
              final isSelected = _riskLevel == level;
              Color chipColor;
              switch (level) {
                case "AGGRESSIVE":
                  chipColor = Colors.red.shade600;
                  break;
                case "CONSERVATIVE":
                  chipColor = Colors.blue.shade700;
                  break;
                default:
                  chipColor = const Color(0xFF0F5B44);
              }
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _riskLevel = level),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: isSelected ? chipColor.withOpacity(0.12) : Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: isSelected ? chipColor : Colors.grey.shade200, width: isSelected ? 2 : 1),
                    ),
                    child: Center(
                      child: Text(
                        level,
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: isSelected ? chipColor : Colors.black38, letterSpacing: 0.5),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0F5B44),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              icon: const Icon(Icons.play_arrow, color: Colors.white),
              label: const Text("Run Simulation", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
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
        balance: _balanceCtrl.text.isNotEmpty ? double.tryParse(_balanceCtrl.text) : null,
        riskLevel: _riskLevel,
      );
      if (mounted) setState(() => _simResult = result);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Simulation error: $e"), backgroundColor: Colors.red));
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
    final overrides = _simResult?['scenario_overrides'] as Map<String, dynamic>? ?? {};

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
        boxShadow: [BoxShadow(color: healthColor.withOpacity(0.08), blurRadius: 12)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.insights, color: Color(0xFF0B3B2E), size: 20),
              const SizedBox(width: 8),
              const Text("Simulation Results", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF0B3B2E))),
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
                decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(8)),
                child: Text("${e.key}: ${e.value}", style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600)),
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
                  decoration: BoxDecoration(color: healthColor.withOpacity(0.06), borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      Text("$healthScore", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: healthColor)),
                      const Text("Health Score", style: TextStyle(fontSize: 10, color: Colors.black45)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      Text(runway != null ? "$runway" : "∞", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.blue.shade700)),
                      const Text("Runway (days)", style: TextStyle(fontSize: 10, color: Colors.black45)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Recommendation badge
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: healthColor.withOpacity(0.06),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: healthColor.withOpacity(0.2)),
            ),
            child: Row(
              children: [
                Icon(Icons.lightbulb, color: healthColor, size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Recommended Strategy", style: TextStyle(fontSize: 10, color: Colors.black45)),
                      Text(recommendation, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: healthColor)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Overall recommendation text
          if (overallRec.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: Colors.grey.shade50, borderRadius: BorderRadius.circular(14)),
              child: Text(
                overallRec.length > 500 ? "${overallRec.substring(0, 500)}..." : overallRec,
                style: const TextStyle(fontSize: 11, color: Colors.black54, height: 1.5),
              ),
            ),
        ],
      ),
    );
  }

  String _formatCurrency(double amount) {
    if (amount >= 10000000) return "₹${(amount / 10000000).toStringAsFixed(1)}Cr";
    if (amount >= 100000) return "₹${(amount / 100000).toStringAsFixed(1)}L";
    if (amount >= 1000) return "₹${(amount / 1000).toStringAsFixed(1)}K";
    return "₹${amount.toStringAsFixed(0)}";
  }
}
