# Risk Management & Capital Preservation

## Risk Principles
The scanner prioritizes capital preservation over frequency of trades. Even high-scoring setups can fail in adverse market environments.

---

## Position Sizing Formulas

Users input:
- Account Capital (e.g. ₹1,00,000)
- Risk Per Trade % (default: $0.75\%$)

### Step 1: Maximum Risk Budget
$$\text{Max Risk Budget} = \text{Account Capital} \times \text{Risk Per Trade}$$
*Example:* For ₹1,00,000 capital at 0.75% risk, maximum loss is ₹750.

### Step 2: Risk Per Share
$$\text{Risk Per Share} = \text{Entry Price} - \text{Stop Loss}$$
*Example:* Entry ₹500, Stop ₹485 $\implies$ Risk = ₹15 per share.

### Step 3: Unconstrained Quantity
$$\text{Quantity}_{\text{risk}} = \left\lfloor \frac{\text{Max Risk Budget}}{\text{Risk Per Share}} \right\rfloor = \left\lfloor \frac{750}{15} \right\rfloor = 50\text{ shares}$$

### Step 4: Single Position Capital Cap (25%)
To prevent catastrophic concentration if a stock has a very tight stop:
$$\text{Max Position Capital} = \text{Account Capital} \times 25\%$$
$$\text{Quantity}_{\text{cap}} = \left\lfloor \frac{\text{Max Position Capital}}{\text{Entry Price}} \right\rfloor$$
$$\text{Final Quantity} = \min(\text{Quantity}_{\text{risk}}, \text{Quantity}_{\text{cap}})$$

---

## Portfolio Level Safeguards

1. **Maximum Open Positions:** Default: 5 positions simultaneously.
2. **Maximum Portfolio Open Risk:** Total capital exposed to risk across all open trades cannot exceed $3.0\%$.
3. **Sector Concentration Limit:** No more than 2 positions in the same sector.
